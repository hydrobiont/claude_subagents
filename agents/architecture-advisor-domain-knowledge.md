# Architecture Advisor — Domain knowledge

Persistent notes accumulated by the `architecture-advisor` agent across invocations. The agent reads this file at the start of every run and appends entries when it learns something durable about the domain.

This file is **distinct from** `architecture-advisor-criteria.md`: that file is the evaluation rubric (what to check against). This file is the agent's accumulated *findings* (what it has learned about specific technologies, ecosystems, vendors, and decision patterns). Criteria are how it judges; domain knowledge is what it knows.

See the agent definition (`architecture-advisor.md`) for the rules on what belongs here vs not.

<!-- entries below; newest on top -->

### Slack Socket Mode vs HTTP — production stance (2026-07)
Slack docs: "we recommend using HTTP for production applications" for highest reliability, but "As long as you do not intend to submit your app to the Slack Marketplace and actively maintain your connection … Socket Mode is a reliable option." Limit: 10 concurrent WebSocket connections per app. Marketplace/distributed apps MUST use HTTP. No deprecation signals. `bolt-python` `SocketModeHandler` defaults `auto_reconnect_enabled=True`; historical edge-case reconnect bugs (bolt-python #470, python-slack-sdk #1379). Socket→HTTP switch under Bolt = swap adapter + stand up public endpoint + signature-verify; listener logic unchanged. Source: docs.slack.dev/apis/events-api/comparing-http-socket-mode/.

### Slack Connect external-member interaction matrix
App installed only in the host workspace, channel shared via Slack Connect: external members CANNOT invoke slash commands or message actions ("not shared — limited only to the team that has installed the app"); they CAN click buttons/dropdowns (validate `authorized_users` in the interaction payload); bot users can DM external users who share a channel; `app_mention` fires for external members' mentions. Ephemeral delivery (`chat.postEphemeral`) and button-triggered modals (`views.open`) to external members are NOT confirmed by docs — test in the real workspace. Source: docs.slack.dev/apis/slack-connect/.

### Slack + Odoo client-library maintenance (2026-07)
`slack-bolt` (Python) v1.29.0 and `slack-sdk` v3.43.0 both released 2026-06-30, Slack-employee maintained (seratch / WilliamBergamin / zimeg), support Python 3.7–3.14. `bolt-js` v4.7.3. No official Slack Go SDK — `slack-go/slack` is community (nlopes/kanata2), still pre-1.0 (v0.27.0) after ~10y, and there is no Bolt-for-Go. `OdooRPC` is effectively solo-maintained (sebalix 231 commits vs next contributor 5 = 46×), last PyPI release 0.10.1 on 2023-08-16, moved osiell→OCA without a fresh release; prefer stdlib `xmlrpc.client` for thin Odoo adapters.

### GitHub Actions Node-20 deprecation
Node 24 becomes the Actions default 2026-06-16; Node 20 is removed fall 2026. Remediation: bump `actions/checkout` (→v6) and `webfactory/ssh-agent` (→v0.10.0) to land on Node-24 runtimes before the cutoff.

### PHP / Ubuntu EOL reference (as of 2026-06)
PHP 7.4 EOL 2022-11-28; 8.2 security support to 2026-12-31, 8.3 to 2027-12-31. Ubuntu 20.04 standard support ended 2025-05, ESM to 2030-04 via Ubuntu Pro (free for ≤5 machines).

### WordPress deploy architecture for code-only pipelines
When only the theme / mu-plugins are git-managed and content + plugins live in wp-admin, rsync-over-SSH beats containers or Bedrock — the immutable slice is too small to justify either. The mutable runtime state (DB, uploads, ad-hoc-installed plugins) dominates and neither tool addresses it.
