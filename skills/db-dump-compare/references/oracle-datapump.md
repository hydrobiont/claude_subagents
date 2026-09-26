# Oracle Data Pump (expdp) exports: what can be read without Oracle

## The log is the primary source
```
Export: Release 19.0.0.0.0 - Production on Tue Aug 11 11:30:23 2026   <- client release + start time
Version 19.28.0.0.0                                                   <- Release Update level (19.28 = July 2025 RU)
Connected to: Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
;;;  parfile:  full=Y | schemas=... | tables=...                      <- export mode
;;;  parfile:  parallel=3, flashback_time=SYSTIMESTAMP                <- flashback_* => consistent snapshot
Starting "SYS"."SYS_EXPORT_FULL_01":  "/******** AS SYSDBA" parfile=...
Processing object type DATABASE_EXPORT/SCHEMA/TABLE/TABLE_DATA        <- one line per object type that had objects
. . exported "PASX"."AUDITTRAILENTRY"          1.000 GB 6978340 rows  <- per table (or ":"PARTITION")
Master table "SYS"."SYS_EXPORT_FULL_01" successfully loaded/unloaded
Dump file set for SYS.SYS_EXPORT_FULL_01 is: /path/file_01.dmp ...
Job "SYS"."SYS_EXPORT_FULL_01" successfully completed at ... elapsed 0 00:13:15
```
- Sizes are binary units (GB = 1024^3). `exported` lines give data volume and rows per
  table; metadata objects (packages, views, triggers) appear only as object-type lines,
  without owner or count. Owner-level detail needs `impdp ... SQLFILE=` on an Oracle host.
- Materialized views: the container table is listed as an exported table.
- `ORA-` lines anywhere = warnings/errors; "completed with N error(s)" in the job line.
- `Total estimation using BLOCKS method` appears only when ESTIMATE was requested.
- A FULL export includes Oracle-maintained schemas (SYS, SYSTEM, WMSYS, AUDSYS, OUTLN,
  DBSNMP, CTXSYS, XDB, MDSYS, ...). Classify them separately from application schemas.

## Dump-file header (first 4 KB, readable with xxd/strings)
Observed on 19c files:
- bytes 0-1: dump-file format version (`05 01` = 5.1). Format version -> writer:
  0.1 = 10.1, 1.1 = 10.2, 2.1 = 11.1, 3.1 = 11.2, 4.1 = 12.1, 5.1 = 12.2/18c/19c/21c/23ai.
- byte 0x22 (little-endian 16-bit): file number within the set (1, 2, 3 ...).
- 0x43: `"OWNER"."JOB_NAME"`.
- later strings: platform (`x86_64/Linux 2.4.xx` is the constant Linux x86-64 label),
  instance name, database character set (`AL32UTF8`), internal DB version marker
  (`19.05.00.00.00` on 19c files), master-table marker `NNN:NNN:NNNNNN:NNNNNN`
  (`000:000:...` = this file holds no master table; `001:001:000001:000001` = it does).
  The file with the master table is the one impdp must read first.
- `file` misidentifies these as "PDP-11 old overlay"; ignore that.

## Inside the files
- Metadata (DDL as XML) is zlib-compressed by default (`COMPRESSION=METADATA_ONLY`), so
  object names of packages/views are not greppable.
- Table data is uncompressed unless `COMPRESSION=ALL|DATA_ONLY`; check: sum of logged table
  bytes / sum of file sizes near 1.0 => uncompressed. Encrypted dumps show no readable strings.
- Each table's data stream starts with an uncompressed XML header
  `<STRMTABLE_T>...<CHARSET>AL32UTF8</CHARSET><NCHARSET>AL16UTF16</NCHARSET><DBTIMEZONE>GMT</DBTIMEZONE>
  ...<OWNER_NAME>PASX</OWNER_NAME><NAME>TABLE</NAME>...<COL_LIST>...</STRMTABLE_T>` (column
  names, TYPE_NUM 1 = VARCHAR2, 2 = NUMBER, 12 = DATE, 180 = TIMESTAMP, 113 = BLOB, 112 = CLOB).
  Rows follow; VARCHAR2 values are readable (a length byte precedes each), NUMBER/DATE are binary.
  `scripts/dmp_find_table_stream.py` locates a header and dumps the strings of that stream.
- NLS facts come free from those headers: DB charset, national charset, DB time zone.

## Version vocabulary
- "Release 19.0.0.0.0" is the release family; "Version 19.28.0.0.0" is the Release Update
  (quarterly; 19.28 = 19.28.0.0.250715, July 2025). The client and database usually share
  the Oracle Home, so the RU shown is the database patch level.
- Edition ("Enterprise Edition") matters for feature use (partitioning, advanced compression).
