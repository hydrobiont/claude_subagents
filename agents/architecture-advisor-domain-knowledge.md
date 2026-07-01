# Architecture Advisor — Domain knowledge

Persistent notes accumulated by the `architecture-advisor` agent across invocations. The agent reads this file at the start of every run and appends entries when it learns something durable about the domain.

This file is **distinct from** `architecture-advisor-criteria.md`: that file is the evaluation rubric (what to check against). This file is the agent's accumulated *findings* (what it has learned about specific technologies, ecosystems, vendors, and decision patterns). Criteria are how it judges; domain knowledge is what it knows.

See the agent definition (`architecture-advisor.md`) for the rules on what belongs here vs not.

<!-- entries below; newest on top -->

### GitHub Actions Node-20 deprecation
Node 24 becomes the Actions default 2026-06-16; Node 20 is removed fall 2026. Remediation: bump `actions/checkout` (→v6) and `webfactory/ssh-agent` (→v0.10.0) to land on Node-24 runtimes before the cutoff.

### PHP / Ubuntu EOL reference (as of 2026-06)
PHP 7.4 EOL 2022-11-28; 8.2 security support to 2026-12-31, 8.3 to 2027-12-31. Ubuntu 20.04 standard support ended 2025-05, ESM to 2030-04 via Ubuntu Pro (free for ≤5 machines).

### WordPress deploy architecture for code-only pipelines
When only the theme / mu-plugins are git-managed and content + plugins live in wp-admin, rsync-over-SSH beats containers or Bedrock — the immutable slice is too small to justify either. The mutable runtime state (DB, uploads, ad-hoc-installed plugins) dominates and neither tool addresses it.
