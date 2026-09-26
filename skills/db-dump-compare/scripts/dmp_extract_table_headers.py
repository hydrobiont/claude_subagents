#!/usr/bin/env python3
"""Harvest the physical column definitions of every table in an Oracle Data Pump dump set
from the uncompressed <STRMTABLE_T> data-stream headers - no Oracle instance needed.

Each table data stream begins with an XML header listing OWNER_NAME, NAME and, per column,
NAME, TYPE_NUM (Oracle internal type code), LENGTH, PRECISION_NUM, SCALE, NOT_NULL,
CHARSETID, CHARSETFORM (2 = national character set), CHARLENGTH. This gives the source-side
type of every column, which is what a data-migration type-mapping review needs. Sequential
full read of the files (about 5 minutes for 176 GB on a laptop SSD). Read-only.

Usage: dmp_extract_table_headers.py --out headers.json [--md summary.md] file1.dmp file2.dmp ...
"""
import argparse, collections, json, os, re, sys, time

TYPE_NAMES = {1: "VARCHAR2", 2: "NUMBER", 8: "LONG", 12: "DATE", 23: "RAW", 24: "LONG RAW", 58: "OPAQUE/XMLTYPE",
              69: "ROWID", 96: "CHAR", 100: "BINARY_FLOAT", 101: "BINARY_DOUBLE", 105: "MLSLABEL", 108: "OBJECT",
              109: "OBJECT/ANYDATA", 111: "REF", 112: "CLOB", 113: "BLOB", 114: "BFILE", 122: "NESTED TABLE",
              123: "VARRAY", 178: "TIME", 179: "TIME WITH TZ", 180: "TIMESTAMP", 181: "TIMESTAMP WITH TIME ZONE",
              182: "INTERVAL YEAR TO MONTH", 183: "INTERVAL DAY TO SECOND", 208: "UROWID", 231: "TIMESTAMP WITH LOCAL TIME ZONE"}
HDR = re.compile(rb"<STRMTABLE_T>(.*?)</STRMTABLE_T>", re.S)
COL = re.compile(rb"<COL_LIST_ITEM>(.*?)</COL_LIST_ITEM>", re.S)


def tag(x, name, default=None):
    m = re.search(rb"<" + name + rb">(.*?)</" + name + rb">", x)
    return m.group(1).decode("latin1").strip() if m else default


def type_name(c):
    n = int(c["type_num"])
    base = TYPE_NAMES.get(n, f"TYPE_{n}")
    if n in (1, 96) and c.get("charsetform") == "2": base = "N" + base  # NVARCHAR2 / NCHAR
    if n == 2:
        p, s = c.get("precision"), c.get("scale")
        if p: return f"NUMBER({p}{',' + s if s not in (None, '0') else ''})"
        if s == "0": return "NUMBER(*,0)"
        return "NUMBER"
    if n in (1, 96, 23): return f"{base}({c.get('charlength') or c.get('length')})"
    if n in (180, 181, 231): return f"{base}({c.get('scale')})" if c.get("scale") else base
    return base


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+"); ap.add_argument("--out", required=True); ap.add_argument("--md"); ap.add_argument("--chunk-mb", type=int, default=64)
    a = ap.parse_args()
    CH = a.chunk_mb << 20; OV = 2 << 20
    tables = {}; streams = collections.Counter(); t0 = time.time(); done = 0; total = sum(os.path.getsize(f) for f in a.files); db = {}
    for fn in a.files:
        with open(fn, "rb", buffering=0) as f:
            prev = b""
            while True:
                buf = f.read(CH)
                if not buf: break
                data = prev + buf
                last_end = 0
                for m in HDR.finditer(data):
                    h = m.group(1); last_end = m.end()
                    owner, name = tag(h, b"OWNER_NAME"), tag(h, b"NAME")
                    if not owner or not name: continue
                    if not db: db = {"charset": tag(h, b"CHARSET"), "ncharset": tag(h, b"NCHARSET"), "dbtimezone": tag(h, b"DBTIMEZONE")}
                    streams[(owner, name)] += 1
                    if (owner, name) in tables: continue
                    cols = []
                    for cm in COL.finditer(h):
                        c = cm.group(1)
                        col = {"name": tag(c, b"NAME"), "type_num": tag(c, b"TYPE_NUM"), "length": tag(c, b"LENGTH"), "precision": tag(c, b"PRECISION_NUM"),
                               "scale": tag(c, b"SCALE"), "not_null": tag(c, b"NOT_NULL"), "charsetform": tag(c, b"CHARSETFORM"), "charlength": tag(c, b"CHARLENGTH"),
                               "property": tag(c, b"PROPERTY")}
                        col["type"] = type_name(col); cols.append(col)
                    tables[(owner, name)] = {"owner": owner, "table": name, "obj_num": tag(h, b"OBJ_NUM"), "property": tag(h, b"PROPERTY"), "columns": cols,
                                             "file": os.path.basename(fn)}
                # keep an overlap large enough to hold a header that straddles the boundary
                cut = max(len(data) - OV, last_end) if last_end else len(data) - OV
                prev = data[max(cut, 0):] if len(data) > OV else data
                # an unterminated header at the tail must be kept whole
                j = data.rfind(b"<STRMTABLE_T>")
                if j >= 0 and data.find(b"</STRMTABLE_T>", j) < 0: prev = data[j:]
                done += len(buf)
                if (done // CH) % 128 == 0: print(f"  {done / (1 << 30):.0f}/{total / (1 << 30):.0f} GB, {len(tables)} tables", file=sys.stderr, flush=True)
    out = {"db": db, "tables": sorted(tables.values(), key=lambda t: (t["owner"], t["table"])), "streams_per_table": {f"{o}.{n}": c for (o, n), c in streams.items()},
           "scanned_files": [os.path.abspath(f) for f in a.files], "seconds": round(time.time() - t0)}
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"{len(tables)} tables, {sum(len(t['columns']) for t in tables.values())} columns, {sum(streams.values())} streams, {out['seconds']}s -> {a.out}")
    if a.md:
        by_owner = collections.defaultdict(collections.Counter)
        for t in tables.values():
            for c in t["columns"]: by_owner[t["owner"]][re.sub(r"\(.*\)", "", c["type"])] += 1
        L = ["# Oracle column types per schema (from Data Pump stream headers)", "", f"DB charset {db.get('charset')}, NCHAR {db.get('ncharset')}, DB time zone {db.get('dbtimezone')}", ""]
        for o, cnt in sorted(by_owner.items(), key=lambda x: -sum(x[1].values())):
            L += [f"## {o}: {sum(1 for t in tables.values() if t['owner'] == o)} tables, {sum(cnt.values())} columns", "", "| type | columns |", "|---|---|"] + [f"| {k} | {v} |" for k, v in cnt.most_common()] + [""]
        open(a.md, "w").write("\n".join(L))


if __name__ == "__main__":
    main()
