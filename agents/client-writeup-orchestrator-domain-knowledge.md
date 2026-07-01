# Client Write-up Orchestrator — Domain knowledge

Persistent notes for the `client-writeup-orchestrator` agent. The agent reads this file at the start of every invocation and appends durable learnings (per-customer voice preferences, the user's recurring reshape patterns, verification sources that paid off, workspace-layout facts) under the marker below — newest on top.

---

## Seed facts (2026-06)

### Workspace layout
`~/work/de/clients/<customer>/` — one folder per customer; `*-internal` / `*_internal` = Data Egret internal notes repo, most with their own `.git`. Year subfolders (`2024/`–`2026/`) and per-engagement folders (e.g. `finteqhub_internal/2025/DBA-169/`) are common. Prior deliverables sit next to new ones (e.g. `pricemoov/dataegret_pricemoov_report_v1.0/`) — read them for voice and structure before drafting. The workspace root is NOT a git repo; the customer folders mostly ARE — hence the iron rule that the user commits manually.

### The QA pair
- **Fact pass:** `training-fact-checker` agent — charter says training slides, so re-scope per invocation (target file, "client write-up", explicit verification sources). Returns per-claim verdicts, never edits. Fallback: `general-purpose` seeded with the verdict-table methodology.
- **Style pass:** `tighten-prose` skill at `~/.claude/skills/tighten-prose/SKILL.md` — per-word deletion test; never cuts identifiers, version qualifiers, negations, numbers, command output, or deliberate voice.

### Downstream compile
`client-report-builder` turns a finished report into branded HTML + PDF via `~/.dataegret/markdown-converter/converter.sh` — it requires the standard YAML frontmatter. Hand off only when the user declares the write-up final.

<!-- entries below; newest on top -->
