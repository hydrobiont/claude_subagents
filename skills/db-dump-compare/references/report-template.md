# Report template (fill every line; write "not verifiable from the dump" where true)

## Versions
| | side A | side B |
|---|---|---|
| engine + edition | Oracle Database 19c EE 19.0.0.0.0 | PostgreSQL 14.22 |
| patch level / minor | RU 19.28 (July 2025) | 14.22 (26 Feb 2026 out-of-cycle) |
| dump tool + format | expdp 19.28, Data Pump file format 5.1 | pg_dump 14.22, archive 1.14-0, directory, gzip |
| how verified | log banner + string inside .dmp header | pg_restore -l header + raw toc.dat strings |

## Dump properties
mode (full / schemas / tables), consistency (flashback_time / single transaction), created at,
size on disk, compression, encryption, character set / encoding / locale, platform, instance/dbname.

## Content
schemas (application vs engine-internal), tables, tables with data, empty tables, rows total,
data volume, largest tables (by volume and by rows), object types present (code objects!),
extensions, large objects, roles referenced.

## Comparison
schema mapping, tables only on one side (with rows), row-count agreement (identical / differing
with deltas / both empty), materialized views, schemas out of scope on one side, provenance
conclusion (same snapshot? fresh install + load?).

## Application-level version markers
Liquibase / Flyway history: install date, upgrade dates, highest release directory, tool version;
vendor config tables.

## Verification pairs that agreed / disagreed
one line each.

## Open questions for the next step
