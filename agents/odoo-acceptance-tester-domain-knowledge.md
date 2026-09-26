# Odoo Acceptance Tester — Domain knowledge

## 2026-08-14 — STANDING RULE (user directive): Stripe = ONE designated sandbox only

The user opened a single Stripe **Sandbox** (account uses Google Workspace SSO;
no standalone credentials exist) for the course-booking integration.
**All Stripe work — configuration, keys, webhooks, test payments — happens
ONLY inside that one sandbox. Never live mode, never another sandbox, never
account-level settings.** Verify the sandbox context before ANY Stripe action;
if the dashboard is not in that sandbox, stop and report.
Sandbox identity + key storage (1Password dataegretgmbh vault item
"Stripe SANDBOX … — course booking PoC"; macOS Keychain services
`stripe-sandbox-secret` / `stripe-sandbox-publishable`) are pinned in
browser-operator's domain knowledge from its first-entry report.
Off-prod Odoo builds receive sandbox keys only (the re-arm runbook asserts the
`sk_test_` prefix and refuses anything else). Live keys enter Odoo production
only at the user-gated go-live step, entered by the user.

Persistent notes accumulated by the `odoo-acceptance-tester` agent across invocations. The agent reads this file at the start of every run and appends durable findings — verified odoo.sh/Odoo platform behaviour, upgrade and `noupdate` quirks, per-module surface inventories, reliable ways to observe build and test results, and traps that cost a round.

**Never stored here:** any API key, token or secret value (**1Password via `op read` is now the store** — user directive 2026-08-04; the legacy Odoo API key still sits in the macOS keychain as `odoo-sh-dataegret-api`), ephemeral run state (that belongs in the run's report under `~/work/de/odoo/migration/scratchpad/acceptance/`), or generic testing advice. Programme state lives in `~/work/de/odoo/migration/CLAUDE.md`, `PROGRESS-LOG.md` and the `PLAN-*.md` set.

**HARD RAIL: production is READ-ONLY to this agent.** Write-path testing happens on a staging or `dev/*` build. Every verdict names the database it was observed on.

**★ Standing rule of this programme:** figures written in any document — including this one — are orientation, NOT evidence. Re-read every number live from the API before asserting it. Build ids, URLs and database names rotate on every rebuild.

<!-- entries below; newest on top -->

### 2026-08-04 — A 403 from `odoo.dataegret.com` may be Cloudflare, not Odoo: a FALSE-RED trap, and the host your probes must name
The dataegret Odoo is reachable on **two hostnames serving the same database**: `odoo.dataegret.com` (Cloudflare-**proxied**, zone `dataegret.com`, plan Pro) and `dataegret.odoo.com` (straight to odoo.sh `207.175.22.251`, **no proxy**). A Cloudflare WAF block returns **403 plus a "Sorry, you have been blocked" HTML page** and the request **never reaches Odoo** — so the assertion fails, the odoo.sh log shows nothing, and the obvious conclusion (the feature is broken) is wrong. This is the mirror image of the false-green traps listed below: a **false red** that will cost a round.

**Rules for this agent:**
- **Probe `dataegret.odoo.com`** when you are testing Odoo behaviour. It bypasses the WAF entirely, so a non-200 is genuinely Odoo's.
- If you must use `odoo.dataegret.com` (e.g. verifying invite/reset links, which `web.base.url` pins to that host with `web.base.url.freeze = True`), **attribute every non-200 by the response `server:` header** — `cloudflare` means the edge answered, `Odoo.sh` means the origin did. Never report a verdict on a 4xx without that check.
- The block page prints the **zone apex** (*"You are unable to access dataegret.com"*) regardless of the subdomain requested — it is not the WordPress site.
- **Name the hostname in the verdict**, alongside the database, exactly as the programme already requires for the DB.

**Survivability angle:** this control lives in Cloudflare, **outside the repo and outside Odoo**, so a module update (`-u`) or an Odoo version upgrade will not reset it — but neither will a repo rollback restore it. As of 2026-08-04 a host-scoped rule skips the **OWASP Core Ruleset** for `odoo.dataegret.com` (entrypoint `1d994ae8beb241c4bd895e0b1684f420`, rule 1) while the Cloudflare Managed Ruleset stays active. If portal, 2FA (`/web/login/totp`), report-download or ticket-form endpoints start 403-ing again, check that rule still exists and still sits **ahead of** the `execute` rules before suspecting the module.

### 2026-07-27 — Seed: environments, and how to observe a build's real test result

**Environments** (re-resolve live from `CLAUDE.md` every run; ids rotate):
| Role | URL | db | Keychain service |
|---|---|---|---|
| **Production** (read-only to you) | `https://dataegret.odoo.com` | `dataegret-odoo-prod-34639522` | `odoo-sh-dataegret-api` |
| Staging fork of prod | `https://dataegret-staging-migration-<build>.dev.odoo.com` | same-named db | same key (travels with the fork) |
| `dev/*` build | `https://dataegret-dev-<branch>-<build>.dev.odoo.com` | same-named db | same key |
| Cloud trial (source + rollback anchor) | `https://dataegret-trial.odoo.com` | `dataegret-trial` | `odoo-dataegret-api` |

Login `ik@dataegret.com`, **uid 2** on every one of them — assert the uid AND the db name after authenticating, because the URLs are similar enough to mix up and the prod one is the one you must not write to. Odoo `19.0+e`. Addons repo `github.com/dataegret/odoo` at `~/work/de/odoo/odoo` (note: *two* `odoo` path segments; `~/work/de/odoo` is the parent workspace, not the repo). Branches: `prod` (production), `staging_migration`, `dev/*`. odoo.sh updates a module on a production/staging build **only when the manifest `version` changes** — a code-only push rebuilds without re-running the module update.

**Reading a build's test result — do not trust the badge.** For `de_slack_notify`, the healthy badge is **"Test: Warning" with the sub-status "done"**, because the module install emits several expected warnings; "Success" is not what a green run looks like here. A red run reads "Test: Failed — At least one test failed when loading the modules (de_slack_notify, ai_account)"; `ai_account` is co-listed incidentally, not a second failure. The authoritative record is in the build container:

```
ssh -i ~/.ssh/odoosh_dataegret_rsa -o StrictHostKeyChecking=no <build-id>@<build-domain> \
    'grep -aE "de_slack_notify: [0-9]+ tests|failed, [0-9]+ error|FAIL:" ~/logs/install.log | tail'
```

The two lines that matter are `odoo.tests.stats: <module>: N tests` and `odoo.tests.result: 0 failed, 0 error(s) of N tests`. Add `-A22` after a `FAIL:` match to get the traceback. Notes: use `-a` (the log trips binary detection); `~/logs/` holds `install.log`, `odoo.log`, `pip.log`; **sftp/scp are disabled** so push a file with `ssh '<cmd> > file' < local`; and `odoo-bin shell`/single-test runs on the container need an explicit `--addons-path` including `/src/odoo/addons,/src/enterprise,/src/user`. A `<string>:38: (ERROR/3) Unexpected indentation.` line is pre-existing docutils noise from RST in a manifest description — present on green builds too, not a finding.

The module-loading line (`Module X: N failures, 0 errors of N tests`) counts only at-install tests, while `odoo.tests.result` counts the whole run including `post_install` classes — the two totals legitimately differ; quote the one you mean.

### 2026-07-27 — Seed: `noupdate` is the survivability crux, and this codebase already gets it right

Records loaded from a module's data files are **reset to their file values on every module update** unless the record or its enclosing `<data>` block carries `noupdate="1"`. The sharpest instance: a cron that **ships disabled** and was enabled by hand in production gets **switched back off by the next update**, silently stopping a live feature with no error in any log.

Verified 2026-07-27: both custom modules already wrap their cron in `noupdate="1"` with an explicit comment naming the active flag as the operational lever — `de_slack_notify/data/ir_cron.xml` ("the active flag is the go-live lever and must survive updates") and `de_gmail_crm_sync/data/ir_cron.xml`. Confirmed empirically the same day: two consecutive prod module updates (19.0.1.x → 2.0.0 → 2.1.0) left the live cron `active=True` and its 5-minute interval intact. **Re-check this on every run anyway** — a new data file, or a `<data>` block added without the flag, reintroduces the hazard, and reading the XML is cheap.

Things that are ordinary DB rows and therefore survive updates (confirm, don't assume — and check the module doesn't re-seed a default over a live value): `ir.config_parameter` values (cursors, tokens, channel names, cutoff boundaries), user-created records, and the modules' own marker/cache fields. Things re-applied on update: view arch, menus, ACL rows, `ir.rule` domains, and any non-`noupdate` data record. If the spec expects an operator to tune something that lives in a non-`noupdate` data record, that is a design defect worth reporting even when today's values happen to match.

### 2026-07-27 — Seed: `de_slack_notify` surface (subject of the first specs)

Module `de_slack_notify` in the addons repo; **19.0.2.1.0** as of 2026-07-27 (v1 feed live on prod since 07-24, v2 digests since 07-27). Two features in one cron:

- **v1 — channel feed** (`models/slack_notify.py`): `de.slack.notify` AbstractModel, cron "Slack: sales/billing notifications" every 5 min. Deal created / stage moved / WON / LOST / internal note / inbound customer email → `#sales`, one digest per deal per pass; posted customer invoice reaching paid/in_payment → `#billing` with a `de.slack.notified.payment` dedup row (dormant until accounting go-live). Window is `(cursor, now − settle]` with a settle buffer; a failed post **holds the cursor** so the next pass retries.
- **v2 — personal DM digests** (`models/slack_digest.py`): `de.slack.digest.reminder`, ≤5 active per user, daily (current day) or weekly (current ISO calendar week, grouped by day), `send_time` as a float in the **user's own timezone**; own-records `ir.rule`; UI at **CRM ▸ Configuration ▸ Slack Digest**. Fires once per slot (`last_sent_slot`: `YYYY-MM-DD` daily, `YYYY-Www` weekly); fires at *or after* the send time on the same local day, so a send time already past today delivers on the **next cron pass**; a DM failure leaves the slot unconsumed to retry. Overdue section capped at 10 + "…and N more"; overdue prefixes carry the year, in-window items do not. Setting/updating/pausing/removing a reminder DMs the owner a confirmation, which is cosmetic by contract (Slack failure is logged and swallowed so it can never block a save). Slack member id resolved via `users.lookupByEmail` and cached on `res.users.de_slack_member_id` (manually overridable).

Params: `de_slack_notify.` + `bot_token` / `sales_channel` / `billing_channel` / `internal_domains` / `settle_seconds` / `cursor`. Slack app "DE Sales Notify" with `chat:write` + `im:write` + `users:read.email`; **the bot must be a member of every channel it posts to**, and reinstalling the app rotates the token (keychain `de-slack-notify-bot-token` plus the prod and staging params — rotate all three together or the feed sits in hold-and-retry).

Deterministic seams for testing: `de.slack.digest.reminder._process_due(now_utc)` takes an injected clock, and `_slack_call`/`_slack_post` are the patch points the module's own tests use. `_cron_notify` is private and **not RPC-callable** — trigger a pass with `ir.cron.method_direct_trigger`. There is a read-only iteration helper at `~/work/de/odoo/migration/scripts/slack_digest_devtool.py` (`list` / `preview` / `rearm --apply` / `fire --apply`) whose `preview` renders a real digest from live data without sending anything.

### 2026-07-27 — Seed: test traps in this codebase that produce FALSE GREEN

Four of these have already cost rounds; the first is the dangerous one because it makes tests pass while asserting nothing.

1. **Context propagates through a recordset.** A fixture created with a suppression flag (`with_context(de_slack_no_confirm=True).create(...)`) carries that flag into every later `write()`/`unlink()` on the returned recordset — silently disabling the behaviour under test. Scope such flags to the single call and clear them on what you hand back.
2. **Precommit semantics.** `mail.tracking.value` rows materialize in a **precommit hook**, which a rollback-only test transaction never reaches: `flush_all()` alone leaves zero tracking rows. Worse, records created *and* written inside the same precommit window get **no field tracking at all** (the `mail.tracking.create.*` marker). Tests must `flush + env.cr.precommit.run()` after the create. Production is unaffected because every HTTP request commits.
3. **Odoo itself sends mail during fixtures.** Assigning an activity to another user triggers a real assignment email, so a read-only guard baselined *before* fixtures fails for a reason that has nothing to do with the code. Baseline after fixtures.
4. **Accounting tests need `AccountTestInvoicingCommon`** (a bare test DB has no journals) and `post_install`.
5. **`active_test` hides archived rows from your counts.** On a model with an `active` field, `search`/`search_count` with a plain domain **silently excludes archived records** — observed 2026-07-27 counting digest reminders as 2 when three existed (one paused). Any assertion about "how many records exist", and any check that a record survived an update, must pass `("active", "in", [True, False])` or `context={"active_test": False}`. A paused record that you cannot see is indistinguishable from one that was deleted.

Also: a passing staging rehearsal proves *mechanics*, not *content*. Two real user-facing defects in the v2 digest (dates with no year across a >12-month overdue list; a "Nothing scheduled — enjoy!" line printed under 16 overdue items) survived 36 green tests and a clean rehearsal, and were caught only by rendering the feature against production-scale data. When a spec makes a claim about what a human will read, render it from real data before believing it.

### 2026-07-27 — Seed: programme rails that constrain how you may test

Prod carries the migrated business dataset and **is the system of record** — the migration was declared finished 2026-07-10 and no prod data changes are permitted without the user's explicit per-change approval. The standing invariant is that automation never mails a customer: chatter is written with `mail.message.create()` (never `message_post()`), with no `partner_ids`, and every writing script snapshots `mail.mail` + `mail.notification` before and after and aborts on drift. Tracked-model writes additionally thread a no-track context (`tracking_disable`, `mail_notrack`, `mail_create_nosubscribe`, `mail_create_nolog`, `mail_auto_subscribe_no_notify`) because DBA tickets and tasks carry the customer as a follower and a plain stage write would notify them. Prod's mail queue cron has been the remaining send-gate; treat every prod write as mail-capable regardless.

Other rails: Odoo AUP ~1 call/second with no parallelism; stdlib-only Python (system `python3`, no venv, no third-party packages); idempotency via `ir.model.data` xmlids in module `migration`; single-writer discipline (the check-then-create idempotency is **not** atomic — two concurrent writers produced three orphan duplicate messages once); and source systems (Jira/Tempo/Pipedrive/easybill) are export-only. The prod API key in keychain `odoo-sh-dataegret-api` **expires 2026-10-06**; a sudden auth failure across every environment is a key-expiry symptom, not a code defect.
