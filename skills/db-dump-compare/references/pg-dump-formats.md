# pg_dump outputs: formats, headers, TOC grammar

## Detect the format
| format | on disk | detection |
|---|---|---|
| directory (`-Fd`) | folder with `toc.dat` + `<dumpId>.dat` / `.dat.gz` / `.dat.lz4` / `.dat.zst` (PG16+ lz4/zstd) | `toc.dat` starts with `PGDMP` |
| custom (`-Fc`) | single file, TOC at the END (after data) | starts with `PGDMP` |
| tar (`-Ft`) | single tar with `toc.dat` and members | `ustar` at offset 257 |
| plain | SQL text, optionally gzipped | starts with `--` / `-- PostgreSQL database dump` |

## Binary header (custom file or toc.dat)
`PGDMP` + vmaj, vmin, vrev + intSize + offSize + format byte, then compression, creation
timestamp (sec, min, hour, mday, mon, year-1900, isdst as sign-prefixed ints), dbname, server
version string, pg_dump version string (`WriteHead()` in pg_backup_archiver.c).
- Format byte: 1 custom, 3 tar, 5 directory - but a directory dump's `toc.dat` is written
  with the TAR code on purpose ("The TOC of a directory format dump shares the format code of
  the tar format", pg_backup_directory.c). Do not call a directory dump "tar" because of it.
- Compression: archive versions below 1.15 store the gzip LEVEL as an int (-1 default, 0 none,
  1-9); pg_restore 16+ prints only the algorithm name ("gzip"), so the level (e.g. `-Z 9`) is
  visible only in the raw header. From 1.15 (PG 16) the header stores the algorithm byte
  (0 none, 1 gzip, 2 lz4, 3 zstd).
`pgdump_inventory.py` decodes all of this byte-exactly and prints it next to the `pg_restore -l`
values, which is the built-in second source for versions, date, dbname and compression.
Archive version -> pg_dump major that writes it (src/bin/pg_dump/pg_backup_archiver.h):
1.12 = 9.0-10, 1.13 = 11, 1.14 = 12-15, 1.15 = 16, 1.16 = 17-18. `pg_restore` reads older
archive versions but refuses newer ones ("unsupported version (1.16) in file header"): use a
newer client (Homebrew `libpq` ships the latest `pg_restore`).

## `pg_restore -l` header fields
```
; Archive created at 2026-08-13 10:12:54 CEST
;     dbname: pasx
;     TOC Entries: 19121
;     Compression: gzip            (PG16+: -1 / gzip / lz4 / zstd / none)
;     Dump Version: 1.14-0
;     Format: DIRECTORY
;     Integer: 4 bytes / Offset: 8 bytes
;     Dumped from database version: 14.22
;     Dumped by pg_dump version: 14.22
```
Entry grammar: `<dumpId>; <catalogOid> <objectOid> <TYPE> <schema|-> <name> <owner>`.
Multi-word types include `TABLE DATA`, `FK CONSTRAINT`, `SEQUENCE SET`, `DEFAULT ACL`,
`MATERIALIZED VIEW DATA`, `ACL <subtype>`, `COMMENT <subtype>`. Counting `TABLE` vs
`TABLE DATA` tells schema-only (`-s`) from schema+data; `SEQUENCE SET` entries carry
sequence values; `BLOBS`/`BLOB METADATA`/`LARGE OBJECT` mean large objects were dumped.

## Directory-format data members
- File name = TOC dumpId of the `TABLE DATA` (or `MATERIALIZED VIEW DATA`) entry.
- Content = `COPY ... FROM stdin` text: one line per row, embedded newlines escaped as `\n`,
  NULL as `\N`, then a `\.` line and two empty lines (`archputs("\\.\n\n\n")` in pg_dump).
  Rows = lines before `\.`; `wc -l` over-counts by 3. An empty table gzips to ~25 bytes.
- `gzip -t` over all members is a cheap integrity check; a decode error means a truncated copy.
- Compressed size is a poor proxy for table size; rows are exact.

## What a pg_dump never contains
Roles, role memberships, tablespaces, `ALTER SYSTEM` settings (use `pg_dumpall -g` or
`pg_dumpall --globals-only`). Role names still leak through `ACL`, `DEFAULT ACL` and owner
columns. `CREATE DATABASE ... ENCODING/LOCALE/LC_COLLATE/LC_CTYPE/ICU_LOCALE` is stored in
the archive since PG 11 and emitted only with `pg_restore -C`; `pgdump_inventory.py` greps
it out of the TOC blob so encoding and collation are known without restoring.

## Reading small tables
`gzip -dc <dumpId>.dat.gz | head` gives the rows; the column order is the `CREATE TABLE`
statement in `toc.dat` (`strings toc.dat | grep -A30 'CREATE TABLE schema.table ('`).
