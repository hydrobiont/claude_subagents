# Training Fact-Checker — Domain knowledge

Persistent notes accumulated by the `training-fact-checker` agent across invocations. The agent reads this file at the start of every run and appends entries when it learns something durable about the domain — e.g. PG history facts that recur across chapters (with verified sources), claims that have been pre-verified once and can be trusted on sight, common slide-authoring pitfalls (e.g. confusing GUC defaults across versions), high-quality primary sources for given topics, etc.

See the agent definition (`training-fact-checker.md`) for the rules on what belongs here vs not.

<!-- entries below; newest on top -->

### PG 18 EXPLAIN ANALYZE output changes (version-sensitive, 2026)
Two v18 changes to verify on any EXPLAIN-bearing slide that may have been copied from a pre-v18 transcript: (1) **BUFFERS is auto-enabled with ANALYZE** — `EXPLAIN ANALYZE` shows `Buffers:` lines without `(BUFFERS)`. Release note "Automatically include BUFFERS output in EXPLAIN ANALYZE" (Guillaume Lelarge, David Rowley, commit c2a4078eb). Source: `src/backend/commands/explain_state.c` ~L180 `es->buffers = (buffers_set) ? es->buffers : es->analyze;`. (2) **Actual rows now print with 2 decimals** — `explain.c:1844` formats actual `rows=%.2f` (e.g. `rows=7435.00 loops=1`); estimated rows stay `%.0f` (`explain.c:1799`). A transcript showing integer actual rows (`rows=7435`) is pre-v18. Option parsing moved from `explain.c` to `explain_state.c` in v18 (grep there for BUFFERS/timing/summary defaulting).

### SQL function inlining is a PLANNER step, not the rewriter (PG)
Common slide imprecision: attributing SQL-function inlining to the rewriter alongside view expansion. Views/rules expansion is the rewriter (`query-path.html` "rewrite system... realization of views"). But `inline_function` / `inline_set_returning_function` live in `src/backend/optimizer/util/clauses.c` and `optimizer/prep/prepjointree.c` — i.e. the **planner/optimizer**. Flag IMPRECISE when a slide lists "inlinable SQL functions" under the rewriter stage.

### Canonical `library` dataset row counts (DEVPG test instance)
From `~/.claude/projects/-Users-ik-work-de-trainings2025/memory/test_database_schema.md`: **books = 70 050 rows** (68 MB), authors 2 050, copies 240 077, members 30 100, loans 1 120 890, reservations 570 050, reviews 565 050. Use for fast internal-arithmetic checks of dev-01/dev-03 EXPLAIN transcripts (e.g. `Rows Removed by Filter` + kept rows should sum to the table total) without needing the live tunnel. Live re-execution of exact buffer/dirtied/timing numbers is `training-sql-tester`'s job.
