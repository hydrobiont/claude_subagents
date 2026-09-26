#!/usr/bin/env python3
"""Compare two dump inventories (JSON from expdp_inventory.py / pgdump_inventory.py).

Matches schemas (case-insensitive, or via --schema-map ORA=pg), then compares
table name sets and per-table row counts. Row counts on the Oracle side come
from the expdp log; on the PostgreSQL side from --count-rows in
pgdump_inventory.py (directory format). Materialized views show up as tables
in expdp logs (their container table is exported as TABLE_DATA) but as
MATERIALIZED VIEW in pg_dump TOCs; the report annotates that.

Usage:
  compare_dumps.py --a ora.json --b pg.json [--schema-map PASX=pasx ...] [--md OUT] [--json OUT] [--show N]
"""
import argparse, collections, json


def load_tables(inv):
    """-> {schema_lower: {table_lower: {"name":..., "rows": int|None, "bytes": float|None, "kind": ...}}}, label"""
    out = collections.defaultdict(dict)
    if inv.get("kind") == "oracle_datapump":
        for e in inv["aggregate"]["per_table"]:
            out[e["schema"].lower()][e["table"].lower()] = {"name": e["table"], "rows": e["rows"], "bytes": e["bytes"], "kind": "TABLE_DATA"}
        return out, f"Oracle Data Pump ({inv['log'].get('database_banner', '?')})"
    if inv.get("kind") == "postgresql_dump":
        types_seen = set()
        for t in inv.get("tables", []):  # data members (directory format) carry rows
            out[t["schema"].lower()][t["table"].lower()] = {"name": t["table"], "rows": t.get("rows"), "bytes": t.get("compressed_bytes"),
                                                             "kind": "MATERIALIZED VIEW" if t["type"].startswith("MATERIALIZED") else "TABLE"}
        # tables without data members (schema-only dumps / custom format): fall back to TOC entries if present
        for e in inv.get("toc_tables", []):
            out[e["schema"].lower()].setdefault(e["name"].lower(), {"name": e["name"], "rows": None, "bytes": None, "kind": "TABLE"})
        return out, f"PostgreSQL dump ({inv.get('toc_header', {}).get('dumped_from_database_version', '?')}, {inv.get('format')})"
    raise SystemExit("unknown inventory kind")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a", required=True); ap.add_argument("--b", required=True)
    ap.add_argument("--schema-map", nargs="*", default=[], help="A_SCHEMA=B_SCHEMA pairs (case-insensitive)")
    ap.add_argument("--md"); ap.add_argument("--json"); ap.add_argument("--show", type=int, default=40)
    a = ap.parse_args()
    A, la = load_tables(json.load(open(a.a))); B, lb = load_tables(json.load(open(a.b)))
    smap = {x.split("=")[0].lower(): x.split("=")[1].lower() for x in a.schema_map}
    for s in A:
        if s not in smap and s in B: smap[s] = s
    md = ["# Dump comparison", "", f"- A: {la} (`{a.a}`)", f"- B: {lb} (`{a.b}`)", ""]
    res = {"schema_map": smap, "schemas": []}
    unmapped_a = [s for s in A if s not in smap]; unmapped_b = [s for s in B if s not in smap.values()]
    md += ["## Schema mapping", "", "| A schema | B schema | A tables | B tables |", "|---|---|---|---|"]
    for sa, sb in smap.items(): md.append(f"| {sa} | {sb} | {len(A[sa])} | {len(B.get(sb, {}))} |")
    if unmapped_a:
        md += ["", "Schemas only in A (not compared):", ""]
        for s in unmapped_a:
            t = A[s]; md.append(f"- {s}: {len(t)} tables, {sum(x['rows'] or 0 for x in t.values()):,} rows" + (f", {sum(x['bytes'] or 0 for x in t.values()) / (1 << 30):.1f} GB" if any(x['bytes'] for x in t.values()) else ""))
    if unmapped_b:
        md += ["", "Schemas only in B (not compared):", ""] + [f"- {s}: {len(B[s])} tables" for s in unmapped_b]
    for sa, sb in smap.items():
        ta, tb = A[sa], B.get(sb, {})
        common = sorted(set(ta) & set(tb)); only_a = sorted(set(ta) - set(tb)); only_b = sorted(set(tb) - set(ta))
        ident = [t for t in common if ta[t]["rows"] is not None and tb[t]["rows"] is not None and ta[t]["rows"] == tb[t]["rows"]]
        diff = sorted([t for t in common if ta[t]["rows"] is not None and tb[t]["rows"] is not None and ta[t]["rows"] != tb[t]["rows"]],
                      key=lambda t: -abs(ta[t]["rows"] - tb[t]["rows"]))
        uncomparable = [t for t in common if ta[t]["rows"] is None or tb[t]["rows"] is None]
        both_empty = [t for t in common if ta[t]["rows"] == 0 and tb[t]["rows"] == 0]
        r = {"a": sa, "b": sb, "common": len(common), "only_a": only_a, "only_b": only_b, "identical_rows": len(ident),
             "differing_rows": [{"table": t, "a_rows": ta[t]["rows"], "b_rows": tb[t]["rows"], "delta": tb[t]["rows"] - ta[t]["rows"]} for t in diff],
             "uncomparable": len(uncomparable), "both_empty": len(both_empty),
             "a_rows_common": sum(ta[t]["rows"] or 0 for t in common), "b_rows_common": sum(tb[t]["rows"] or 0 for t in common)}
        res["schemas"].append(r)
        md += ["", f"## {sa} (A) vs {sb} (B)", "",
               f"- Tables: A {len(ta)}, B {len(tb)}, common {len(common)}, only in A {len(only_a)}, only in B {len(only_b)}",
               f"- Row counts on common tables: identical {len(ident)}, differing {len(diff)}, not comparable {len(uncomparable)}, empty on both sides {len(both_empty)}",
               f"- Rows in common tables: A {r['a_rows_common']:,} vs B {r['b_rows_common']:,} (delta {r['b_rows_common'] - r['a_rows_common']:+,})"]
        if only_a:
            md += ["", f"### Only in A ({len(only_a)})", ""]
            md += [f"- {ta[t]['name']} ({ta[t]['rows']:,} rows)" + (f" -- exists in B as {tb_kind}" if (tb_kind := next((B[sb][x]['kind'] for x in B.get(sb, {}) if x == t), None)) else "") for t in only_a[:a.show]]
        if only_b:
            md += ["", f"### Only in B ({len(only_b)})", ""] + [f"- {tb[t]['name']} [{tb[t]['kind']}]" + (f" ({tb[t]['rows']:,} rows)" if tb[t]['rows'] is not None else "") for t in only_b[:a.show]]
        # matviews in B whose name matches a table in A (reported as "only in A" above since kinds differ? no: names match -> common)
        mv_common = [t for t in common if tb[t]["kind"] == "MATERIALIZED VIEW"]
        if mv_common: md += ["", f"Note: {len(mv_common)} common names are MATERIALIZED VIEWs in B but tables (MV container tables) in A: " + ", ".join(tb[t]['name'] for t in mv_common)]
        if diff:
            md += ["", f"### Differing row counts ({len(diff)}, largest delta first)", "", "| table | A rows | B rows | delta |", "|---|---|---|---|"]
            md += [f"| {ta[t]['name']} | {ta[t]['rows']:,} | {tb[t]['rows']:,} | {tb[t]['rows'] - ta[t]['rows']:+,} |" for t in diff[:a.show]]
    out = "\n".join(md) + "\n"
    if a.md: open(a.md, "w").write(out)
    if a.json: json.dump(res, open(a.json, "w"), indent=1)
    print(out)


if __name__ == "__main__":
    main()
