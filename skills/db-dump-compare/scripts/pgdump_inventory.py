#!/usr/bin/env python3
"""Inventory a PostgreSQL dump: directory (-Fd), custom (-Fc), tar (-Ft) or plain SQL.

Read-only. Reports server + pg_dump versions, archive format version, creation
time, database name, CREATE DATABASE settings, TOC entries by object type,
schemas, owners, extensions, large objects, and (directory format, --count-rows)
exact per-table row counts by decompressing each data member. Row counts come
from the COPY text stream: rows = lines before the `\\.` terminator (pg_dump
appends `\\.` plus two empty lines to every data member, so `wc -l` is +3).

Usage:
  pgdump_inventory.py <dump-dir | dump.pgdump | dump.sql[.gz]> [--count-rows] [--jobs N]
                      [--pg-restore PATH] [--json OUT] [--md OUT] [--top N]
"""
import argparse, collections, concurrent.futures, datetime, glob, gzip, json, os, re, shutil, subprocess, sys

MULTIWORD = sorted(["TABLE DATA", "FK CONSTRAINT", "SEQUENCE SET", "SEQUENCE OWNED BY", "DEFAULT ACL", "MATERIALIZED VIEW DATA",
                    "MATERIALIZED VIEW", "LARGE OBJECT", "BLOB METADATA", "EVENT TRIGGER", "INDEX ATTACH", "FOREIGN TABLE",
                    "FOREIGN DATA WRAPPER", "USER MAPPING", "TEXT SEARCH CONFIGURATION", "TEXT SEARCH DICTIONARY",
                    "TEXT SEARCH PARSER", "TEXT SEARCH TEMPLATE", "OPERATOR CLASS", "OPERATOR FAMILY", "ROW SECURITY",
                    "PROCEDURAL LANGUAGE", "SHELL TYPE", "PUBLICATION TABLE", "PUBLICATION TABLES IN SCHEMA", "SECURITY LABEL",
                    "ACCESS METHOD", "STATISTICS", "DATABASE PROPERTIES", "TABLE ATTACH", "CONSTRAINT", "TRIGGER", "INDEX",
                    "TABLE", "VIEW", "SEQUENCE", "FUNCTION", "PROCEDURE", "AGGREGATE", "TYPE", "DOMAIN", "SCHEMA", "EXTENSION",
                    "DATABASE", "COLLATION", "CAST", "RULE", "POLICY", "SERVER", "PUBLICATION", "SUBSCRIPTION", "BLOBS", "BLOB",
                    "OPERATOR", "CONVERSION", "TRANSFORM", "ACL", "COMMENT", "ENCODING", "STDSTRINGS", "SEARCHPATH"],
                   key=len, reverse=True)
# pg_dump archive format version -> pg_dump major versions writing it (src/bin/pg_dump/pg_backup_archiver.h)
ARCHIVE_VERSIONS = {"1.12": "9.0 - 10", "1.13": "11", "1.14": "12 - 15", "1.15": "16", "1.16": "17 - 18"}
FORMAT_BYTE = {1: "custom", 3: "tar (directory-format toc.dat shares this code)", 5: "directory", 0: "unknown"}
COMPRESSION_ALGO = {0: "none", 1: "gzip", 2: "lz4", 3: "zstd"}
PG_RESTORE_CANDIDATES = ["pg_restore", "/opt/homebrew/opt/libpq/bin/pg_restore", "/usr/local/opt/libpq/bin/pg_restore"] + \
    sorted(glob.glob("/opt/homebrew/opt/postgresql@*/bin/pg_restore"), reverse=True) + \
    sorted(glob.glob("/usr/lib/postgresql/*/bin/pg_restore"), reverse=True) + sorted(glob.glob("/usr/pgsql-*/bin/pg_restore"), reverse=True)


def detect(path):
    if os.path.isdir(path):
        return "directory" if os.path.exists(os.path.join(path, "toc.dat")) else None
    with open(path, "rb") as f: head = f.read(512)
    if head.startswith(b"PGDMP"): return "custom"
    if head[257:262] == b"ustar" or b"toc.dat" in head: return "tar"
    if path.endswith(".gz"):
        with gzip.open(path, "rb") as f: head = f.read(512)
    return "plain" if head.lstrip().startswith(b"--") or b"PostgreSQL database dump" in head else None


def raw_header(path):
    """Byte-exact parse of the archive header (custom file or toc.dat), mirroring ReadHead() in
    src/bin/pg_dump/pg_backup_archiver.c: magic, version, intSize, offSize, format, compression,
    creation time, dbname, server version, pg_dump version. Independent of pg_restore."""
    with open(path, "rb") as f: b = f.read(8192)
    h = {}
    if not b.startswith(b"PGDMP"): return h
    pos = [5]
    def byte():
        v = b[pos[0]]; pos[0] += 1; return v
    def rint(size):  # WriteInt: sign byte, then intSize little-endian magnitude bytes
        neg = byte(); v = int.from_bytes(b[pos[0]:pos[0] + size], "little"); pos[0] += size
        return -v if neg else v
    def rstr(size):  # WriteStr: length as WriteInt (-1 = NULL), then bytes
        n = rint(size)
        if n < 0: return None
        v = b[pos[0]:pos[0] + n].decode("utf-8", "replace"); pos[0] += n; return v
    vmaj, vmin, vrev = byte(), byte(), byte()
    h["magic"] = "PGDMP"; h["archive_version"] = f"{vmaj}.{vmin}"; h["archive_revision"] = vrev
    h["archive_version_written_by_pg_dump"] = ARCHIVE_VERSIONS.get(h["archive_version"], "unknown mapping")
    h["int_size"] = byte(); h["offset_size"] = byte(); fmt = byte(); h["format_byte"] = fmt; h["format"] = FORMAT_BYTE.get(fmt, fmt)
    isz = h["int_size"]
    if (vmaj, vmin) >= (1, 15):
        h["compression_algorithm"] = COMPRESSION_ALGO.get(byte(), "?")
    else:
        lvl = rint(isz); h["compression_level"] = lvl
        h["compression_algorithm"] = "none" if lvl == 0 else f"gzip level {lvl if lvl > 0 else 'default (-1)'}"
    sec, mn, hr, mday, mon, year, isdst = (rint(isz) for _ in range(7))
    h["created_at"] = f"{year + 1900:04d}-{mon + 1:02d}-{mday:02d} {hr:02d}:{mn:02d}:{sec:02d}" + (" (DST)" if isdst else "")
    h["dbname"] = rstr(isz); h["server_version_string"] = rstr(isz); h["pg_dump_version_string"] = rstr(isz)
    return h


def find_pg_restore(pref):
    cands = ([pref] if pref else []) + PG_RESTORE_CANDIDATES
    out = []
    for c in cands:
        p = shutil.which(c) if os.sep not in c else (c if os.path.exists(c) else None)
        if p and p not in out: out.append(p)
    return out


def run_toc(path, pg_restores):
    last = None
    for pr in pg_restores:
        r = subprocess.run([pr, "-l", path], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout: return pr, r.stdout, None
        last = f"{pr}: {r.stderr.strip()}"
    return None, "", last or "no pg_restore found"


def parse_toc(text):
    hdr, entries = {}, []
    for ln in text.splitlines():
        if ln.startswith(";"):
            m = re.match(r"^;\s+([A-Za-z_ ]+?):\s+(.*)$", ln)
            if m: hdr[m.group(1).strip().lower().replace(" ", "_")] = m.group(2).strip()
            m = re.match(r"^; Archive created at (.*)$", ln)
            if m: hdr["created_at"] = m.group(1)
            continue
        m = re.match(r"^(\d+); (\d+) (\d+) (.*)$", ln)
        if not m: continue
        rest = m.group(4)
        typ = next((k for k in MULTIWORD if rest.startswith(k + " ")), rest.split()[0])
        tail = rest[len(typ) + 1:].split()
        owner = tail[-1] if tail else ""
        schema = tail[0] if tail else ""
        name = " ".join(tail[1:-1]) if len(tail) > 2 else ""
        if typ in ("ACL", "COMMENT"):  # e.g. "ACL - SCHEMA pasx pasx", "COMMENT pasx COLUMN t.c pasx"
            sub = tail[1] if len(tail) > 1 else ""
            name = " ".join(tail[2:-1])
            typ = f"{typ} {sub}"
        entries.append({"dump_id": int(m.group(1)), "catalog_oid": int(m.group(2)), "oid": int(m.group(3)),
                        "type": typ, "schema": schema, "name": name, "owner": owner})
    return hdr, entries


def find_create_database(path):
    """Locate the CREATE DATABASE statement text inside toc.dat / a custom-format file (TOC is at the end of custom files)."""
    size = os.path.getsize(path); chunk = 32 << 20; pos = size
    with open(path, "rb") as f:
        while pos > 0:
            start = max(0, pos - chunk); f.seek(start); b = f.read(min(chunk + 4096, size - start))
            i = b.find(b"CREATE DATABASE ")
            if i >= 0:
                stmt = b[i:i + 1024].split(b";")[0].decode("utf-8", "replace")
                sets = re.findall(rb"ALTER DATABASE [^;]{0,300};", b[i:i + 20000])
                return stmt + ";", [s.decode("utf-8", "replace") for s in sets]
            pos = start
    return None, []


def count_rows_file(fn):
    """rows in a directory-format data member = COPY lines before the `\\.` terminator."""
    opener = gzip.open if fn.endswith(".gz") else open
    n = 0
    try:
        if fn.endswith(".lz4") or fn.endswith(".zst"):
            tool = ["lz4", "-dc"] if fn.endswith(".lz4") else ["zstd", "-dc"]
            p = subprocess.Popen(tool + [fn], stdout=subprocess.PIPE)
            for ln in p.stdout:
                if ln == b"\\.\n": break
                n += 1
            p.wait()
            return fn, n, None if p.returncode == 0 else f"{tool[0]} exit {p.returncode}"
        with opener(fn, "rb") as f:
            for ln in f:
                if ln == b"\\.\n": break
                n += 1
        return fn, n, None
    except Exception as e:
        return fn, None, str(e)


def plain_inventory(path):
    opener = gzip.open if path.endswith(".gz") else open
    inv = {"header": {}, "statements": collections.Counter(), "copy_tables": [], "insert_rows": collections.Counter()}
    in_copy = None; n = 0; cur_table = None
    with opener(path, "rt", encoding="utf-8", errors="replace") as f:
        for ln in f:
            if in_copy:
                if ln == "\\.\n": inv["copy_tables"].append({"table": in_copy, "rows": n}); in_copy = None
                else: n += 1
                continue
            if ln.startswith("-- Dumped from database version"): inv["header"]["dumped_from_database_version"] = ln.split(":", 1)[1].strip()
            elif ln.startswith("-- Dumped by pg_dump version"): inv["header"]["dumped_by_pg_dump_version"] = ln.split(":", 1)[1].strip()
            elif ln.startswith("COPY "):
                in_copy = re.match(r"^COPY (\S+)", ln).group(1); n = 0
            elif ln.startswith("INSERT INTO "):
                inv["insert_rows"][re.match(r"^INSERT INTO (\S+)", ln).group(1)] += 1
            else:
                m = re.match(r"^(CREATE (?:OR REPLACE )?(?:UNLOGGED |MATERIALIZED |UNIQUE )?[A-Z ]+?|ALTER TABLE|COMMENT ON|GRANT|REVOKE|SET |SELECT pg_catalog\.setval)\b", ln)
                if m: inv["statements"][m.group(1).strip()] += 1
    inv["statements"] = dict(inv["statements"]); inv["insert_rows"] = dict(inv["insert_rows"])
    return inv


def fmt_bytes(b):
    for u, d in (("TB", 1 << 40), ("GB", 1 << 30), ("MB", 1 << 20), ("KB", 1 << 10)):
        if b >= d: return f"{b / d:.2f} {u}"
    return f"{int(b)} bytes"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path"); ap.add_argument("--count-rows", action="store_true"); ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--pg-restore"); ap.add_argument("--json"); ap.add_argument("--md"); ap.add_argument("--top", type=int, default=20)
    a = ap.parse_args()
    fmt = detect(a.path)
    if not fmt: sys.exit(f"cannot detect dump format of {a.path}")
    inv = {"kind": "postgresql_dump", "path": os.path.abspath(a.path), "format": fmt,
           "generated_at": datetime.datetime.now().isoformat(timespec="seconds")}
    md = [f"# PostgreSQL dump inventory", "", f"- Path: `{inv['path']}`", f"- Format: {fmt}"]
    if fmt == "plain":
        p = plain_inventory(a.path); inv["plain"] = p
        md += [f"- Dumped from database version: {p['header'].get('dumped_from_database_version','?')}",
               f"- Dumped by pg_dump version: {p['header'].get('dumped_by_pg_dump_version','?')}",
               f"- COPY blocks (tables with data): {len(p['copy_tables'])}, rows: {sum(t['rows'] for t in p['copy_tables']):,}",
               f"- INSERT rows: {sum(p['insert_rows'].values()):,} across {len(p['insert_rows'])} tables", "", "| statement | count |", "|---|---|"]
        md += [f"| {k} | {v} |" for k, v in sorted(p["statements"].items(), key=lambda x: -x[1])]
        out = "\n".join(md) + "\n"
        if a.json: json.dump(inv, open(a.json, "w"), indent=1)
        if a.md: open(a.md, "w").write(out)
        print(out); return
    hdr_file = os.path.join(a.path, "toc.dat") if fmt == "directory" else a.path
    inv["raw_header"] = raw_header(hdr_file) if fmt != "tar" else {}
    pr, toc_text, err = run_toc(a.path, find_pg_restore(a.pg_restore))
    inv["pg_restore_used"] = pr; inv["pg_restore_error"] = err
    hdr, entries = parse_toc(toc_text) if toc_text else ({}, [])
    inv["toc_header"] = hdr
    types = collections.Counter(e["type"] for e in entries)
    schemas = collections.Counter(e["schema"] for e in entries if e["schema"] not in ("-", ""))
    owners = collections.Counter(e["owner"] for e in entries)
    tables = [e for e in entries if e["type"] == "TABLE"]
    tdata = [e for e in entries if e["type"] == "TABLE DATA"]
    inv["counts"] = {"toc_entries": len(entries), "by_type": dict(types.most_common()), "schemas": dict(schemas), "owners": dict(owners),
                     "tables": len(tables), "table_data_entries": len(tdata),
                     "extensions": [e["name"] for e in entries if e["type"] == "EXTENSION"],
                     "large_objects": types.get("BLOBS", 0) + types.get("BLOB", 0) + types.get("LARGE OBJECT", 0) + types.get("BLOB METADATA", 0)}
    if fmt != "tar":
        stmt, sets = find_create_database(hdr_file); inv["create_database"] = stmt; inv["alter_database"] = sets
    data_members = []
    if fmt == "directory":
        for e in tdata + [e for e in entries if e["type"] == "MATERIALIZED VIEW DATA"]:
            cands = glob.glob(os.path.join(a.path, f"{e['dump_id']}.dat*"))
            if cands: data_members.append({"dump_id": e["dump_id"], "schema": e["schema"], "table": e["name"], "type": e["type"],
                                            "file": cands[0], "compressed_bytes": os.path.getsize(cands[0])})
        inv["data_members"] = len(data_members); inv["data_bytes_on_disk"] = sum(m["compressed_bytes"] for m in data_members)
        if a.count_rows:
            with concurrent.futures.ThreadPoolExecutor(a.jobs) as ex:
                res = {fn: (n, err) for fn, n, err in ex.map(count_rows_file, [m["file"] for m in data_members])}
            for m in data_members: m["rows"], m["error"] = res[m["file"]]
    inv["tables"] = [{k: m[k] for k in ("schema", "table", "type", "compressed_bytes", "rows", "error") if k in m} for m in data_members]
    # markdown
    rh = inv["raw_header"]
    md += [f"- Dumped from database version: {hdr.get('dumped_from_database_version','?')} (raw header string: {rh.get('server_version_string')})",
           f"- Dumped by pg_dump version: {hdr.get('dumped_by_pg_dump_version','?')} (raw header string: {rh.get('pg_dump_version_string')})",
           f"- Archive format version: {hdr.get('dump_version','?')} = pg_dump {rh.get('archive_version_written_by_pg_dump','?')}; format byte: {rh.get('format')}",
           f"- Created at: {hdr.get('created_at','?')} (raw header: {rh.get('created_at')}); dbname: {hdr.get('dbname','?')} (raw: {rh.get('dbname')}); compression: {hdr.get('compression','?')} (raw header: {rh.get('compression_algorithm')})",
           f"- TOC entries: {hdr.get('toc_entries','?')} listed by pg_restore ({len(entries)} parsed); pg_restore used: {pr or 'none'}" + (f"; error: {err}" if err else ""),
           f"- CREATE DATABASE: `{inv.get('create_database')}`"]
    for s in inv.get("alter_database", [])[:10]: md.append(f"  - `{s}`")
    md += [f"- Schemas: {', '.join(f'{k} ({v} entries)' for k, v in schemas.most_common())}",
           f"- Owners: {', '.join(f'{k} ({v})' for k, v in owners.most_common())}",
           f"- Extensions: {', '.join(inv['counts']['extensions']) or 'none'}; large-object entries: {inv['counts']['large_objects']}",
           f"- Tables: {len(tables)}; TABLE DATA entries: {len(tdata)} -> {'schema + data' if tdata else 'schema only (no data)'}", "",
           "## TOC entries by type", "", "| type | count |", "|---|---|"] + [f"| {k} | {v} |" for k, v in types.most_common()]
    if fmt == "directory":
        md += ["", f"## Data members", "", f"- {len(data_members)} data files, {fmt_bytes(inv['data_bytes_on_disk'])} on disk (compressed)"]
        if a.count_rows:
            ok = [m for m in data_members if m.get("rows") is not None]
            md += [f"- rows counted: {sum(m['rows'] for m in ok):,} in {len(ok)} members; empty tables: {sum(1 for m in ok if m['rows'] == 0)}; decode errors: {sum(1 for m in data_members if m.get('error'))}",
                   "", f"### Top {a.top} by rows", "", "| table | rows | compressed |", "|---|---|---|"]
            md += [f"| {m['schema']}.{m['table']} | {m['rows']:,} | {fmt_bytes(m['compressed_bytes'])} |" for m in sorted(ok, key=lambda m: -m["rows"])[:a.top]]
        md += ["", f"### Top {a.top} by compressed size", "", "| table | compressed | rows |", "|---|---|---|"]
        md += [f"| {m['schema']}.{m['table']} | {fmt_bytes(m['compressed_bytes'])} | {m.get('rows', 'n/a')} |" for m in sorted(data_members, key=lambda m: -m["compressed_bytes"])[:a.top]]
    out = "\n".join(md) + "\n"
    if a.json: json.dump(inv, open(a.json, "w"), indent=1, default=str)
    if a.md: open(a.md, "w").write(out)
    print(out)


if __name__ == "__main__":
    main()
