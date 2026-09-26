#!/usr/bin/env python3
"""Inventory an Oracle Data Pump (expdp) export: log file + dump-file headers.

Read-only. Works without an Oracle client: everything comes from the expdp log
(versions, parameters, per-table rows/bytes, object types, completion status)
and from the first 4 KB of each .dmp file (format version, file number,
character set, instance, platform, internal DB version marker).

Usage:
  expdp_inventory.py <dir-with-log-and-dmp | path-to-log> [--json OUT] [--md OUT] [--top N]
"""
import argparse, collections, datetime, glob, json, os, re, sys

ORACLE_INTERNAL = {
    "SYS", "SYSTEM", "WMSYS", "AUDSYS", "OUTLN", "DBSNMP", "CTXSYS", "XDB", "MDSYS", "ORDSYS",
    "ORDDATA", "ORDPLUGINS", "OLAPSYS", "LBACSYS", "DVSYS", "DVF", "GSMADMIN_INTERNAL", "GSMUSER",
    "GSMCATUSER", "OJVMSYS", "APPQOSSYS", "DBSFWUSER", "GGSYS", "REMOTE_SCHEDULER_AGENT", "SYSBACKUP",
    "SYSDG", "SYSKM", "SYSRAC", "SYS$UMF", "ANONYMOUS", "XS$NULL", "DIP", "ORACLE_OCM", "FLOWS_FILES",
    "SI_INFORMTN_SCHEMA", "MDDATA", "SPATIAL_CSW_ADMIN_USR", "SPATIAL_WFS_ADMIN_USR", "WKSYS", "WK_TEST",
    "WKPROXY", "EXFSYS", "TSMSYS", "DMSYS", "SCOTT", "HR", "OE", "PM", "IX", "SH", "BI", "PDBADMIN",
}
UNIT = {"GB": 1 << 30, "MB": 1 << 20, "KB": 1 << 10, "bytes": 1}
# Data Pump dump-file format version -> first database release that writes it
# (Oracle Database Utilities, "VERSION" parameter / dump file compatibility).
DP_FILE_VERSIONS = {"0.1": "10.1", "1.1": "10.2", "2.1": "11.1", "3.1": "11.2", "4.1": "12.1", "5.1": "12.2 / 18c / 19c / 21c / 23ai"}

RE_EXPORTED = re.compile(
    r'^\. \. exported "([^"]+)"\."([^"]+)"(?::"([^"]+)")?\s+([\d.]+)\s+(GB|MB|KB|bytes)\s+(\d+) rows\s*$')
RE_PARFILE = re.compile(r'^;;;\s+parfile:\s+(\w+)=(.*)$')
RE_STARTING = re.compile(r'^Starting "([^"]+)"\."([^"]+)":\s+(.*)$')
RE_COMPLETED = re.compile(r'^Job "([^"]+)"\."([^"]+)" (successfully completed|completed with \d+ error\(s\)|stopped[^\n]*?) at (.+?)(?: elapsed (\d+ \d\d:\d\d:\d\d))?\s*$')
RE_ESTIMATE = re.compile(r'^Total estimation using (\w+) method:\s+([\d.]+)\s+(GB|MB|KB|bytes)')


def parse_log(path):
    txt = open(path, encoding="utf-8", errors="replace").read().splitlines()
    info = {"log_file": os.path.abspath(path), "log_lines": len(txt), "parfile": {}, "object_types": [],
            "tables": [], "errors": [], "dump_files": [], "unparsed_exported_lines": []}
    in_dumpset = False
    for i, ln in enumerate(txt):
        s = ln.rstrip()
        if s.startswith("Export: Release"):
            m = re.match(r"^Export: Release (\S+) - (\S+) on (.+)$", s)
            if m:
                info["client_release"], info["client_edition_label"], info["started_on"] = m.groups()
            if i + 1 < len(txt) and txt[i + 1].startswith("Version"):
                info["client_version"] = txt[i + 1].split()[1]
        elif s.startswith("Import: Release"):
            info["kind"] = "impdp"
        elif s.startswith("Connected to:"):
            info["database_banner"] = s[len("Connected to:"):].strip()
        elif RE_PARFILE.match(s):
            k, v = RE_PARFILE.match(s).groups(); info["parfile"][k.lower()] = v.strip()
        elif s.startswith("Processing object type"):
            info["object_types"].append(s[len("Processing object type "):].strip())
        elif s.startswith(". . exported") or s.startswith(". . imported"):
            m = RE_EXPORTED.match(s.replace(". . imported", ". . exported", 1))
            if not m:
                info["unparsed_exported_lines"].append(s); continue
            sch, tab, part, v, u, n = m.groups()
            info["tables"].append({"schema": sch, "table": tab, "partition": part,
                                   "bytes": float(v) * UNIT[u], "size_label": f"{v} {u}", "rows": int(n)})
        elif RE_STARTING.match(s):
            m = RE_STARTING.match(s); info["job_owner"], info["job_name"], info["job_invocation"] = m.groups()
        elif s.startswith("Master table"):
            info["master_table_line"] = s
        elif RE_ESTIMATE.match(s):
            m = RE_ESTIMATE.match(s); info["estimate"] = {"method": m.group(1), "bytes": float(m.group(2)) * UNIT[m.group(3)]}
        elif s.startswith("Dump file set for"):
            in_dumpset = True
        elif in_dumpset and s.startswith("  "):
            info["dump_files"].append(s.strip())
        elif RE_COMPLETED.match(s):
            in_dumpset = False
            m = RE_COMPLETED.match(s)
            info["job_status"], info["completed_at"], info["elapsed"] = m.group(3), m.group(4), m.group(5)
        elif "ORA-" in s or s.startswith("W-") and "ORA-" in s:
            info["errors"].append(s)
        else:
            if in_dumpset and not s.startswith("  "):
                in_dumpset = False
    info.setdefault("kind", "expdp")
    return info


def aggregate(info, top):
    tabs = info["tables"]
    per_table = collections.OrderedDict()
    for t in tabs:  # merge partitions into their table
        k = (t["schema"], t["table"])
        e = per_table.setdefault(k, {"schema": t["schema"], "table": t["table"], "bytes": 0.0, "rows": 0, "partitions": 0})
        e["bytes"] += t["bytes"]; e["rows"] += t["rows"]
        if t["partition"]: e["partitions"] += 1
    pt = list(per_table.values())
    schemas = collections.OrderedDict()
    for e in pt:
        s = schemas.setdefault(e["schema"], {"schema": e["schema"], "tables": 0, "bytes": 0.0, "rows": 0, "empty_tables": 0,
                                             "oracle_internal": e["schema"] in ORACLE_INTERNAL or e["schema"].startswith("APEX_")})
        s["tables"] += 1; s["bytes"] += e["bytes"]; s["rows"] += e["rows"]; s["empty_tables"] += (e["rows"] == 0)
    agg = {
        "table_data_entries": len(tabs), "tables": len(pt), "partitioned_entries": sum(1 for t in tabs if t["partition"]),
        "total_rows": sum(e["rows"] for e in pt), "total_bytes": sum(e["bytes"] for e in pt),
        "empty_tables": sum(1 for e in pt if e["rows"] == 0),
        "schemas": sorted(schemas.values(), key=lambda s: -s["bytes"]),
        "application_schemas": sorted(s["schema"] for s in schemas.values() if not s["oracle_internal"]),
        "top_by_bytes": sorted(pt, key=lambda e: -e["bytes"])[:top],
        "top_by_rows": sorted(pt, key=lambda e: -e["rows"])[:top],
        "per_table": pt,
    }
    return agg


def parse_dmp_header(path):
    with open(path, "rb") as f:
        head = f.read(4096)
    h = {"file": os.path.abspath(path), "size_bytes": os.path.getsize(path)}
    if head.startswith(b"EXPORT:V"):
        h["kind"] = "classic exp (not Data Pump)"; h["banner"] = head[:64].split(b"\n")[0].decode("latin1", "replace")
        return h
    h["kind"] = "Data Pump"
    h["file_format_version"] = f"{head[0]}.{head[1]}"
    h["file_format_written_by"] = DP_FILE_VERSIONS.get(h["file_format_version"], "unknown mapping")
    h["file_number_in_set"] = int.from_bytes(head[0x22:0x24], "little")
    strs = [s.decode("latin1") for s in re.findall(rb"[\x20-\x7e]{4,}", head)]
    for s in strs:
        if re.match(r'^"[^"]+"\."[^"]+"$', s): h["job_name"] = s
        elif re.search(r"/(Linux|Windows|Solaris|AIX|HP-UX|HPUX|Darwin)", s): h["platform"] = s
        elif re.match(r"^\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{2}$", s): h["internal_db_version_marker"] = s
        elif re.match(r"^\d{3}:\d{3}:\d{6}:\d{6}$", s):
            h["master_table_marker"] = s
            h["contains_master_table"] = not s.startswith("000:000")
        elif re.match(r"^(AL32UTF8|AL16UTF16|UTF8|US7ASCII|WE8[A-Z0-9]+|EE8[A-Z0-9]+|CL8[A-Z0-9]+|AR8[A-Z0-9]+|JA16[A-Z0-9]+|ZHS16[A-Z0-9]+|ZHT16[A-Z0-9]+|KO16[A-Z0-9]+|TH8[A-Z0-9]+|VN8[A-Z0-9]+|N8[A-Z0-9]+|[A-Z]{2}8[A-Z0-9]+)$", s):
            h["character_set"] = s
    if "character_set" in h:  # instance name is the string right before the charset
        i = strs.index(h["character_set"]); h["instance_name"] = strs[i - 1] if i > 0 else None
    return h


def fmt_bytes(b):
    for u, d in (("TB", 1 << 40), ("GB", 1 << 30), ("MB", 1 << 20), ("KB", 1 << 10)):
        if b >= d: return f"{b / d:.2f} {u}"
    return f"{int(b)} bytes"


def markdown(inv, top):
    L = inv["log"]; A = inv["aggregate"]; H = inv["dump_headers"]
    o = [f"# Oracle Data Pump export inventory", "",
         f"- Log: `{L['log_file']}`",
         f"- Export client: Release {L.get('client_release','?')} / Version {L.get('client_version','?')} (Release Update level)",
         f"- Source database: {L.get('database_banner','?')}",
         f"- Job: {L.get('job_owner','?')}.{L.get('job_name','?')} started {L.get('started_on','?')}, {L.get('job_status','status unknown')} at {L.get('completed_at','?')}, elapsed {L.get('elapsed') or '?'}",
         f"- Sizes below use binary units as the expdp log does (GB = 1024^3 bytes)",
         f"- Parameters: " + ", ".join(f"{k}={v}" for k, v in L["parfile"].items()),
         f"- Consistency: " + ("flashback_time/flashback_scn set (consistent snapshot)" if any(k.startswith("flashback") for k in L["parfile"]) else "no flashback_* parameter (tables exported at different points in time)"),
         f"- Object types processed: {len(L['object_types'])}; errors/warnings (ORA-) lines: {len(L['errors'])}",
         ""]
    if H:
        o += ["## Dump files", "", "| file | size | fmt version | file # | master table | charset | instance | platform | internal version |", "|---|---|---|---|---|---|---|---|---|"]
        for h in H:
            o.append(f"| {os.path.basename(h['file'])} | {fmt_bytes(h['size_bytes'])} | {h.get('file_format_version','')} ({h.get('file_format_written_by','')}) | {h.get('file_number_in_set','')} | {'yes' if h.get('contains_master_table') else 'no'} | {h.get('character_set','')} | {h.get('instance_name','')} | {h.get('platform','')} | {h.get('internal_db_version_marker','')} |")
        tot = sum(h["size_bytes"] for h in H)
        o += ["", f"Dump set size: {fmt_bytes(tot)}; table data reported in log: {fmt_bytes(A['total_bytes'])} "
              f"(ratio {A['total_bytes'] / tot:.3f} -> {'data NOT compressed (default COMPRESSION=METADATA_ONLY)' if 0.9 <= A['total_bytes'] / tot <= 1.05 else 'data compressed or log incomplete'})", ""]
    o += ["## Content", "",
          f"- Table data entries: {A['table_data_entries']} ({A['tables']} tables, {A['partitioned_entries']} partition entries)",
          f"- Total rows: {A['total_rows']:,}; total table data: {fmt_bytes(A['total_bytes'])}; empty tables: {A['empty_tables']}",
          f"- Application schemas: {', '.join(A['application_schemas'])}", "",
          "| schema | tables | empty | rows | data | Oracle-internal |", "|---|---|---|---|---|---|"]
    for s in A["schemas"]:
        o.append(f"| {s['schema']} | {s['tables']} | {s['empty_tables']} | {s['rows']:,} | {fmt_bytes(s['bytes'])} | {'yes' if s['oracle_internal'] else ''} |")
    o += ["", f"## Top {top} tables by data volume", "", "| table | rows | data |", "|---|---|---|"]
    for e in A["top_by_bytes"]: o.append(f"| {e['schema']}.{e['table']} | {e['rows']:,} | {fmt_bytes(e['bytes'])} |")
    o += ["", f"## Top {top} tables by rows", "", "| table | rows | data |", "|---|---|---|"]
    for e in A["top_by_rows"]: o.append(f"| {e['schema']}.{e['table']} | {e['rows']:,} | {fmt_bytes(e['bytes'])} |")
    o += ["", "## Object types processed (in log order)", ""] + [f"- {t}" for t in L["object_types"]]
    if L["errors"]: o += ["", "## ORA- lines", ""] + [f"- `{e}`" for e in L["errors"][:50]]
    if L["unparsed_exported_lines"]: o += ["", f"## Unparsed 'exported' lines ({len(L['unparsed_exported_lines'])})", ""] + [f"- `{e}`" for e in L["unparsed_exported_lines"][:20]]
    return "\n".join(o) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path"); ap.add_argument("--json"); ap.add_argument("--md"); ap.add_argument("--top", type=int, default=20)
    a = ap.parse_args()
    if os.path.isdir(a.path):
        logs = sorted(glob.glob(os.path.join(a.path, "*.log"))); dmps = sorted(glob.glob(os.path.join(a.path, "*.dmp")) + glob.glob(os.path.join(a.path, "*.DMP")))
    else:
        logs = [a.path]; dmps = sorted(glob.glob(os.path.join(os.path.dirname(a.path) or ".", "*.dmp")))
    if not logs: sys.exit("no expdp log found")
    if len(logs) > 1: print(f"warning: {len(logs)} logs found, using {logs[0]}", file=sys.stderr)
    log = parse_log(logs[0])
    inv = {"kind": "oracle_datapump", "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
           "log": log, "aggregate": aggregate(log, a.top), "dump_headers": [parse_dmp_header(d) for d in dmps]}
    md = markdown(inv, a.top)
    if a.json:
        slim = dict(inv); slim["log"] = {k: v for k, v in log.items() if k != "tables"}
        json.dump(slim, open(a.json, "w"), indent=1, default=str)
    if a.md: open(a.md, "w").write(md)
    print(md)


if __name__ == "__main__":
    main()
