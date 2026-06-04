# PostgreSQL Performance Analyzer — Domain knowledge

Persistent notes accumulated by the `postgres-perf-analyzer` agent across invocations. The agent reads this file at the start of every run and appends entries when it learns something durable about the domain — e.g. perf/eBPF tool quirks on the user's Ubuntu VMs, recurring symptom→cause patterns, kernel-version-specific traps, GUC settings worth checking first, flamegraph-reading heuristics, etc.

See the agent definition (`postgres-perf-analyzer.md`) for the rules on what belongs here vs not.

<!-- entries below; newest on top -->
