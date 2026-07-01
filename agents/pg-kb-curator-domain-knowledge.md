# pg-kb-curator — domain knowledge

Persistent cheat sheet for the `pg-kb-curator` agent. Durable facts about maintaining the
PostgreSQL knowledge base at `/Users/ik/pg_knowledge_base`: source-tree locations worth
re-finding, verification shortcuts, recurring article patterns, and user preferences about
the base. Read at the start of every invocation; append durable learnings as `### heading`
+ one tight paragraph under the marker. Not for ephemeral task state or project facts
(those live in the project's `CLAUDE.md`).

<!-- entries below; newest on top -->

### External sources sit at differing proximity to PostgreSQL; near-axis ones invert the risk (2026-06)
Two `external` sources now exist with very different proximity to the PG axis. #6 (Brendan Gregg, OS/Linux performance) is *off-axis* — its content is plainly not PG. #7 (Use The Index, Luke! / Markus Winand, `https://use-the-index-luke.com/`, free web edition of *SQL Performance Explained*; cross-DB: Oracle, PostgreSQL 9.0–17, SQL Server, MySQL, Db2) is *near-axis* — SQL indexing/optimization methodology (B-tree anatomy, WHERE access vs. filter predicates, join algorithms, clustering/index-only scans, pipelined ORDER BY, top-N). Key rule: the closer an external source overlaps PostgreSQL, the MORE its content looks PG-applicable and the more tempting it is to quote as PG truth — so the "verify PG-specifics against sources 1–4" discipline matters *more* for a near-axis source, not less. Proximity never promotes a source up the ranking; authoritative only for methodology/concepts, never for a PG default/GUC/catalog/plan-shape/version claim. The four-tier ranking stays PG-only.

### External (non-PostgreSQL) trusted sources use `kind: external` and a separate authority axis (2026-06)
The registry spans "PostgreSQL and the technologies in its environment." Non-PG expert references (first one: Brendan Gregg's systems-performance site, source #6, OS layer) get `kind: external` and are authoritative *only within their stated domain* — they sit BESIDE the PG sources (1–4), never above them for a PostgreSQL claim. Citation rule for `external`: specific page URL + retrieval date, name the method/tool; methodology is durable but tool flags/output drift, so cross-check tool specifics against current man pages / installed versions. The four-tier authority ranking is PG-only; external sources are off-axis.
