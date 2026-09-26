---
name: db-dump-compare
description: >-
  Inventory and compare database dumps WITHOUT restoring them: Oracle Data Pump exports
  (expdp .dmp file sets plus their log) and PostgreSQL dumps (pg_dump directory, custom, tar
  or plain SQL). Reports source engine version and patch level, dump tool and archive format
  version, creation time, snapshot consistency, compression, character set / encoding, whether
  data is included, schemas, object counts by type, per-table rows and sizes, empty tables,
  and cross-dump differences (table sets, row counts, materialized views vs tables, schemas
  missing on one side). Use it whenever someone drops dump folders and asks "which version is
  this", "is the data in there", "what is in this dump", "compare the Oracle and Postgres
  dumps", "did the vendor migrate everything", or starts any Oracle-to-PostgreSQL or
  PostgreSQL-to-PostgreSQL migration assessment from dump files - even if they only say
  "have a look at these two dumps". Also use it to read small configuration / version /
  Liquibase-changelog tables straight out of the dump files when no database is available.
---

# db-dump-compare

Purpose: answer "what exactly is in these dumps, from which versions, and do they match"
using only the files on disk. Everything here is read-only; the dumps are never modified.
Work in the scratchpad; write reports there (or where the user asks).

## Scripts (all Python 3, no third-party packages)

| script | input | gives |
|---|---|---|
| `scripts/expdp_inventory.py DIR` | expdp log + `.dmp` files | versions, parameters, consistency, per-table rows/bytes, schema summary, object types, dump-file headers, compression inference |
| `scripts/pgdump_inventory.py PATH [--count-rows]` | pg_dump directory / custom / tar / plain | server + pg_dump versions, archive version, creation time, dbname, CREATE DATABASE settings, TOC by type, schemas, owners, extensions, exact row counts (directory format) |
| `scripts/compare_dumps.py --a A.json --b B.json` | the two JSON inventories | schema mapping, table-set diff, per-table row-count diff, matview annotations |
| `scripts/dmp_find_table_stream.py --owner O --table T *.dmp` | Data Pump files | readable strings of one table's rows (slow: full sequential read) |
| `scripts/dmp_extract_table_headers.py --out h.json *.dmp` | Data Pump files | every table's column list with Oracle types, NOT NULL, lengths (full sequential read); join it with the pg_dump `CREATE TABLE` text for a type-mapping matrix |

Run each with `--help` for options. `--json` and `--md` write machine-readable and
human-readable outputs; the compare step needs the JSON files.

## Workflow

1. **Identify what you have before running anything.** `ls -la`, sizes, `file`, first bytes:
   Data Pump files start with two version bytes (`05 01` = format 5.1) and contain
   `"OWNER"."JOB_NAME"` near offset 0x40; classic `exp` files start with `EXPORT:V`;
   `pg_dump` archives start with `PGDMP`; a directory with `toc.dat` plus `NNNN.dat[.gz]`
   members is `pg_dump -Fd`; plain dumps start with `-- PostgreSQL database dump`.
   Details and field layouts: `references/oracle-datapump.md`, `references/pg-dump-formats.md`.

2. **Run the inventories.** Oracle needs only the log for table-level facts (the `.dmp`
   headers add format version, charset, instance, which file holds the master table).
   PostgreSQL needs a `pg_restore` at least as new as the archive version; the script
   tries PATH, Homebrew `libpq`, `postgresql@N` and PGDG paths and reports which one worked.
   `--count-rows` decompresses every data member (about 12 GB gzip in 3-4 minutes with
   `--jobs 6`); run it in the background for big dumps.

3. **Cross-verify every headline figure with a second, independent source.** A log can
   belong to a different run than the files next to it, and a folder name can lie. Pair:
   version from the log banner with the version string inside the binary header; table data
   volume from the log with the sum of `.dmp` sizes (ratio near 1.0 means data was not
   compressed); TOC `TABLE DATA` count with the number of data members; row totals from the
   log with rows counted in the data members; `pg_restore -l` header with the byte-exact raw
   header (`pgdump_inventory.py` prints both, and the raw header also carries the gzip level).
   State in the report which pairs agreed.

4. **Compare.** `compare_dumps.py` maps schemas case-insensitively (override with
   `--schema-map PASX=pasx`). Read the result as evidence about provenance: identical row
   counts across hundreds of active tables mean both dumps come from the same snapshot;
   deltas confined to `databasechangelog`-style tables mean the target schema was installed
   fresh and then loaded; tables present only on the Oracle side are often materialized-view
   container tables (the script annotates when the same name is a MATERIALIZED VIEW in pg).
   Schemas without a counterpart (interfaces, archives, monitoring users) are the usual
   scope gap in a vendor migration - list them with rows and volume.

5. **When a migration is the goal, harvest column types from both sides.** `dmp_extract_table_headers.py`
   yields the Oracle physical schema without an Oracle instance; the pg_dump `toc.dat` holds the
   `CREATE TABLE` text. Joining them shows the type mapping the target expects (NUMBER(1) to boolean,
   FLOAT to double precision, CLOB to text ...), hidden `SYS_NC...$` columns to ignore, NOT NULL drift,
   and which tables carry LOBs - the LOB share of the volume usually decides the tooling.

6. **Find the application version, not just the engine version.** Look for Liquibase
   (`databasechangelog`: `filename` directories and `dateexecuted` tell install and upgrade
   history, `liquibase` column gives the tool version), Flyway (`flyway_schema_history`), or
   vendor tables named like `*version*`, `*config*`, `installation*`. In a directory dump
   read them with `gzip -dc <dumpId>.dat.gz` (dumpId from `pg_restore -l`). In Data Pump
   files use `dmp_find_table_stream.py`; VARCHAR values are readable, dates and numbers are
   not. Liquibase checksums differ between Liquibase 3.x (`7:`) and 4.x (`8:`), so compare
   changelog *paths*, not md5sums, across sides.

7. **Report** with `references/report-template.md`: versions first, then dump properties,
   content, comparison, verification pairs, open questions. Use one unit system and say
   which (expdp logs use GB = 1024^3; `ls` uses decimal). Say explicitly what could not be
   verified (e.g. which schema owns the PL/SQL packages - the expdp log lists object types
   but not owners; DDL is zlib-compressed inside the dump).

## Pitfalls that cost time

- `awk` prints large sums in scientific notation, so `sort -rn` on them is garbage; do
  aggregations in Python.
- `sort`/`uniq` on binary-derived strings need `LC_ALL=C` or they die with "Illegal byte
  sequence".
- Never `grep -a` or `strings` a 50 GB dump end to end; grep buffers whole "lines" and binary
  data has none. The scan script reads fixed chunks.
- Directory-format data members end with `\.` and two empty lines: `wc -l` is rows + 3.
  The script stops at the `\.` terminator instead.
- A full Data Pump export includes Oracle-maintained schemas (SYS, SYSTEM, WMSYS, AUDSYS...);
  exclude them from application scope but mention them.
- pg_dump never contains roles or tablespaces (those come from `pg_dumpall -g`); grants in
  the TOC still reveal role names.
- Quoted upper-case identifiers in a PostgreSQL TOC (e.g. `VIEW pasx PR_BF`) mean the
  application relies on case-sensitive names; lower/upper twins of the same name can coexist.
