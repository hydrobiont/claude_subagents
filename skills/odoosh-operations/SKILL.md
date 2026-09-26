---
name: odoosh-operations
description: >-
  Operate odoo.sh for Data Egret's `dataegret` project (github.com/dataegret/odoo) safely and
  correctly: find the build for a commit or branch, read the REAL test result instead of
  trusting the status badge, get an SSH or RPC session into a build container or a dev
  database, rehearse a change on the staging fork, and fast-forward a tested commit to
  production with the right verification afterward. Use this whenever odoo.sh, the odoo.sh
  dashboard, the `dataegret` project, a build or build id, a dev build or a staging build, the
  Builds page, a branch's Logs/Shell/Connect tab, `install.log`, the test tally,
  `odoo.tests.result`, "Test: Warning"/"Test: Success"/"Test: Failed", View errors, Rebuild
  versus a plain push, deploying or fast-forwarding to `prod`, SSHing into a build container,
  polling a module's `installed_version`, or "did the module update land" comes up — including
  when the user only pastes a build URL, a branch name, or raw card text and asks "why is this
  red / failed / a warning". Also use it for "how do I get into the dev build's database",
  "trigger this cron on staging", or "push this mail through the gateway on a dev build". Not
  for writing or designing the module's own code (`odoo-module-developer`) and not for
  independent acceptance verdicts (`odoo-acceptance-tester`) — this skill covers the platform
  mechanics around a build and a deploy, not what the change itself should be.
---

# odoo.sh Operations

Operate odoo.sh for Data Egret's Odoo project so any model — sonnet or haiku, with or without
prior context — can find a build, read what it actually did, get a session on a build container
or a dev database, rehearse a change on staging, and move a tested commit to production without
breaking anything or trusting the dashboard's colours. This skill assumes the module code and
its tests already exist: deciding what the code should do belongs to `odoo-module-developer`;
judging whether a finished feature meets its spec belongs to `odoo-acceptance-tester`. Read
`references/traps.md` before calling any build "failed" or "green" — most false alarms in this
project's history trace to a trap catalogued there.

## 1. What odoo.sh is here

Project `dataegret`, repository `github.com/dataegret/odoo`, Odoo `19.0+e` on the paid plan.
Three branch kinds, three different effects from a push:

- **`prod`** — production, the system of record. A push is a fast-forward deploy, never a
  rehearsal.
- **`staging_migration`** — a fork of production for rehearsing a change against realistic
  data. A push updates its database *in place*; only the branch page's **Rebuild** control
  discards it and re-forks a fresh copy of production. Picking the wrong one wastes a rehearsal
  or destroys state you needed to keep (§3e).
- **`dev/<name>`** — a disposable CI build. Every push rebuilds from scratch, installs every
  module in the repository (not just the one you changed) without demo data, runs the full
  test suite, then loads demo data in a separate force-demo pass — your fastest signal, and, read correctly (§3b), your most reliable one.

odoo.sh updates a module's code and data on a production or staging build (the ones that update
in place; a dev build rebuilds from scratch) **only when its manifest `version` field changes** — a code-only push against an unchanged version ships the files, but the running
database never reloads them, no error given. The same rule gates JS asset-bundle regeneration,
and it never auto-installs a brand-new module a build has never seen; a new module needs one
explicit install before its later version bumps can ride this mechanism.

A `dev/*` build installs everything and runs the full test suite first, then runs a separate
force-demo pass afterward — any "is this a demo database" check reads false throughout both
install and the test run (see `references/traps.md`).

Timings, orientation only: a `dev/*` build runs roughly 3–5 minutes; a production update is a
short gap, on the order of 30 seconds of HTTP 503 while the server restarts to load the new
version.

## 2. Rails before you act

- **Production data is read-only to you.** Deploy tested code to `prod` and verify it; never
  create, write, unlink, or trigger a business record there — a data correction is separate and
  user-approved, never a side effect of an operations task.
- **A fast-forward push to `prod` needs the user's explicit go for that change.** A standing
  instruction ("if everything is green, deploy it") covers the change it was given for, not
  whatever comes later.
- **Push and Rebuild on a staging branch are different operations** (§3e) — know which one you
  are about to run.
- **Never re-fork `staging_migration` without checking first.** It has decapitated the Slack
  support bot here — a frozen `ODOO_URL` and a lost HMAC secret, surfacing only as a
  routine-looking 5-minute WARNING, not an obvious outage. Say so before you Rebuild if the bot
  matters to whoever asked for the rehearsal.
- **Never tick Settings ▸ "Block access to the .odoo.com domain".** It breaks every build's own
  health check on this project, for every branch.
- **Secrets are named by location, never carried as values.** odoo.sh API key: macOS keychain,
  service `odoo-sh-dataegret-api`, account `ik@dataegret.com` (`security find-generic-password
  -s odoo-sh-dataegret-api -a ik@dataegret.com -w`). SSH key: `~/.ssh/odoosh_dataegret_rsa`.
  Everything else: 1Password via `op read` at call time. Never echo a secret anywhere,
  including into this skill's own files.
- **Every figure anywhere — including this skill — is orientation, not evidence.** Build ids,
  database names, and build domains rotate on every rebuild; re-read them live before acting on
  them.

## 3. Task recipes

### a. Find the build for a commit or branch

1. Open `https://www.odoo.sh/project/dataegret/builds`, or navigate the sidebar's branch list
   to the branch you want (the branch page shows the same cards plus that branch's full
   history).
2. Match the commit by message or SHA on a build card. Card anatomy: commit message, **Age**
   (time since the build started), **Duration** (how long it ran), a status word (`Test:
   Warning`/`Success`/`Failed` — see §3g for what these mean here), a result badge, **View
   errors**, **Connect**, and **Rebuild**.
3. **Trap:** a hand-built URL for a branch name with a slash (`dev/my-feature`) has rendered
   production's own history before (2026-09-21). The percent-encoded form
   (`/branches/dev%2Fmy-feature/logs`) worked on 2026-09-24, but treat that as luck: confirm the
   branch from the page's own **heading** every time, never from the URL you typed or clicked.
4. The build id (the SSH username for §3c) is visible only on the dashboard — no GitHub commit
   statuses exist on this repository, and no branch-name-derived hostname resolves reliably for
   a build that is not currently live. Read it fresh each time; never reuse one from a previous
   session.

Verify: you can name the build id, its Age/Duration, and its status word, and the page heading
confirms the branch you intended.

### b. Read the real test result

The status badge is not the verdict; `install.log` is. `Test: Warning` with sub-status `done`
is the normal **green** result for this project's modules (several install-time warnings are
expected) — `Success` is not more correct, and a `Failed` badge can name a module with no
actually failing test anywhere in the log (§3g explains why).

1. Open the branch's Logs tab, or read `install.log` over SSH (§3c). The web viewer loads the
   **tail first**; scroll up for earlier phases — a `tail`-only read on the container drops
   them too, so grep the **whole file**.
2. Grep the tally: `odoo.tests.result:` — format `N failed, M error(s) of K tests`. This is the
   whole run, including `post_install`-tagged tests, and can differ from the install-time
   module-loading failure count; say which one you mean.
3. Grep `odoo.tests.stats: <module>:` — format `<module>: N tests` — to confirm your module's
   tests actually ran.
4. Grep ` ERROR ` (a log level, not the word anywhere) and `FAIL:`/`ERROR:` markers; keep ~20
   lines of context after a `FAIL:` hit for its traceback: `grep -aE "<module>: [0-9]+
   tests|failed, [0-9]+ error|FAIL: |ERROR: | ERROR " install.log` (`-a`: the log trips binary-content
   detection without it).
5. The **View errors** panel shows WARNING-and-above lines only, with no tracebacks once the
   tally is clean — a convenience view, not a substitute for the log.
6. Badge-to-log mismatch: a badge can say a module failed while the tally reads `0 failed, 0
   error(s)` — grep still finds the real failure mode, an ERROR-level line logged during that
   module's tests, independent of the tally (odoo.sh fails a module on that line's presence
   alone). See `references/traps.md` for the confirmed case and the fix.

Verify: you can quote the tally line verbatim, the module's own test count, and either the
ERROR/FAIL lines found or state plainly that none exist.

### c. SSH into a build container

1. Get the build id and `.dev.odoo.com` domain from the dashboard (§3a) — never guess or reuse
   either from an earlier session.
2. Run `scripts/odoosh_ssh.sh <build-id> <build-domain> [command]`. It applies the agent-bypass
   recipe so a YubiKey PIV key offered by the local ssh-agent cannot pre-empt the registered
   RSA key (`-o IdentityAgent=none -o IdentitiesOnly=yes`), plus `-o BatchMode=yes -o
   ConnectTimeout=20 -o StrictHostKeyChecking=accept-new -o LogLevel=ERROR`, and a **per-build
   throwaway known_hosts file** (`${TMPDIR:-/tmp}/odoosh-kh-<build-id>`) — never the shared
   `~/.ssh/known_hosts`, because the platform answers port 22 under a different host key before
   the container exists, and pinning that key there would break verification for every later
   build.
3. `sftp`/`scp` are disabled on build containers; push a file by redirecting the command
   itself: `ssh <opts> <build-id>@<domain> 'cat > remote-file' < local-file`.
4. A shell or single-test run needs an explicit
   `--addons-path=/src/odoo/addons,/src/enterprise,/src/user`; the container's binary is
   `/opt/odoo.sh/odoosh/bin/odoo-bin` (`odoo-bin shell -d <db> --addons-path=… --no-http`), and
   the absolute spelling `/home/odoo/src/odoo/addons,/home/odoo/src/enterprise,/home/odoo/src/user`
   appears in this project's records as well — both point at the same tree.

Three timing traps before you conclude anything from a failed connection: sshd may only start
accepting connections *after* the test run has already finished, so an early refusal says
nothing about progress; a build can show connected/finished on the dashboard while still
refusing every connection for several minutes; and, separately, the gateway has refused the
registered key outright on the production container, and since 2026-09-21 on some dev
containers too, with no diagnosed cause. When SSH will not cooperate, fall back to **View
errors** or the build's own **Shell** tab (a browser-rendered terminal for read-only
`grep`/`sed`).

Verify: the command returns the expected log content, or fails with a message naming which trap
it looks like and points at the dashboard fallback.

### d. Get into a dev build's database

There is no `admin/admin` on a dev build.

1. Open the build card's **Connect** link — signs the browser in via single sign-on, no
   password needed.
2. For RPC, set a throwaway password on your own user from the browser's JS console while that
   session is signed in (exact `fetch` call in `references/dev-build-access.md`), then
   authenticate over XML-RPC with it. This invalidates the browser session — sign in again
   through Connect if you still need the UI.
3. Outgoing mail is caught by the platform here — nothing reaches a real inbox. A build's own
   mail alias domain is empty until configured, so inbound-alias routing will not deliver on a
   fresh dev build; drive `mail.thread.message_process` directly over RPC instead
   (`references/dev-build-access.md`).
4. To run a cron once, call `ir.cron.method_direct_trigger` over RPC — a cron's private
   `_cron_*` method is not itself RPC-callable.

Verify: XML-RPC `authenticate` returns a uid on the dev build's own database name (never
`dataegret-odoo-prod-*`), and a read-only `search_read` returns data you recognise as demo
data.

### e. Rehearse on staging

- **Push** `staging_migration` to test a module update against the *existing* rehearsal
  database — cheap, keeps prior state, updates only modules whose version changed.
- **Rebuild** only for a clean copy of current production — it discards the existing database,
  decapitates the support bot (§2), and does not auto-install a module a previous session
  installed by hand but that has not reached production, so it can look like a regression that
  is really just an un-refreshed manual step.
- Crons stay paused on staging by design; trigger the one under test directly with
  `ir.cron.method_direct_trigger` instead of waiting for its schedule.
- Retarget every outward-facing parameter (a Slack channel, a notification address, an upload
  endpoint) at a test target first — staging shares the same path to the outside world as
  production; only the scheduler is paused, not the destination.

Verify: the retargeted parameter reads back as the test target over XML-RPC, and the triggered
cron produced its effect without moving `mail.mail`/`mail.notification` counts against a real
recipient.

### f. Update production

1. Confirm the user's explicit go for this specific change (§2).
2. Fast-forward push: `git push origin <sha>:prod`.
3. Expect a short HTTP 503 window while odoo.sh restarts to load the new version — normal, not
   a failure.
4. Poll `installed_version` over XML-RPC until it changes: `python3
   scripts/poll_module_version.py --url https://dataegret.odoo.com --db <prod db name> --module
   <name> --expect <new version>` (reads the API key from the keychain; never pass one on the
   command line). The production database name is recorded in
   `~/work/de/odoo/migration/CLAUDE.md`; read it there rather than from memory.
5. Verify read-only, once the version confirms: views load (read the live `ir.ui.view.arch_db`,
   not just that the model exists), the shipped data records are present, cron `active`
   flags/intervals are as intended, and every guard is unchanged from before the deploy.
6. Fast-forward the shared checkout: `git -C ~/work/de/odoo/odoo pull --ff-only`.

**The version bump is mandatory, not a formality.** Ship a fix with the version unchanged and
the code lands on disk while the running database keeps executing the old version, nothing
flags it. Also mandatory: any operational lever the change ships (a cron's `active` flag, a
tunable parameter) belongs in a `noupdate="1"` data block — without it, the next update resets
that record to the file's shipped value, silently, which has switched a live cron back off in
this project before.

Verify: `installed_version` read back over XML-RPC matches the new version, and every item in
step 5 is confirmed by a live read, not assumed from the push succeeding.

### g. Recognise false green and false red

Five traps have produced a passing suite that proved nothing (full detail and dates in
`references/traps.md` — read it before trusting green on anything touching these areas):

1. A suppression flag set with `with_context` on a fixture's `create()` rides into every later
   `write()`/`unlink()` on that recordset, quietly disabling the behaviour the rest of the test
   means to exercise.
2. `mail.tracking.value` rows materialize in a precommit hook a rolled-back test never reaches
   — assert only after `flush_all()` and `env.cr.precommit.run()`.
3. Ordinary Odoo behaviour (assigning an activity) sends real mail during fixture setup —
   baseline a no-mail guard after fixtures finish, not before.
4. Accounting assertions need `AccountTestInvoicingCommon` (a bare test database has no chart
   of accounts) and sometimes `post_install`.
5. `active_test` hides archived rows from a plain `search`/`search_count` — an existence or
   count check needs `("active","in",[True,False])` or `context={"active_test": False}`, or a
   paused record looks deleted.

False red: `odoo.dataegret.com` sits behind a Cloudflare WAF in front of the same database
`dataegret.odoo.com` reaches directly. A WAF block returns HTTP 403 with a block page before
Odoo ever sees the request — nothing appears in any odoo.sh log, so a check against the proxied
hostname can read as a broken feature that was never exercised. Probe `dataegret.odoo.com` to
bypass the WAF; if you must use the proxied hostname, read the response's `server:` header
first (`cloudflare` = the edge answered, `Odoo.sh` = the origin did) — and note a block page
names the zone's apex domain regardless of which subdomain triggered it.

Verify: before calling anything definitively broken, rule out which of these six explains the
symptom, or show positive evidence none applies.

## 4. Report the outcome

Use this shape every time, whether the news is good or bad:

- **Build id, branch, commit** — read live, not from memory.
- **Tally line, verbatim** — the `odoo.tests.result:` line exactly as logged.
- **`<module>: N tests`** — the module's own `odoo.tests.stats:` line.
- **ERROR lines** — quote them, or state plainly "none found".
- **Badge** — what the dashboard showed, as a secondary signal, never the verdict.
- **What was verified, and on which database** — name it (dev build, `staging_migration` build,
  or production db); an unnamed database is not a production claim.
- **What was not done** — explicitly. Never let silence imply coverage you lack (a rehearsal
  skipped, a check not run, a cron not triggered).

## 5. Reference files and scripts

- `references/dashboard-and-logs.md` — exact URLs, full card anatomy, log-viewer behaviour,
  complete grep patterns, and how a browser-automation agent should read an odoo.sh page. Read
  before a first dashboard visit or when a grep pattern needs the precise regex.
- `references/dev-build-access.md` — the exact JSON-RPC `fetch` call, an XML-RPC snippet,
  `message_process`/`method_direct_trigger` calls, and what a dev build does and does not have.
  Read before scripting against one.
- `references/staging-and-production.md` — push vs. Rebuild, the production deploy sequence
  with timings, the post-deploy checklist, and the shared-checkout fast-forward. Read before
  any staging or production action beyond §3e/§3f above.
- `references/traps.md` — every dated trap in full, including the five false-green traps
  written out completely. Read whenever a result looks surprising, before reporting it as a
  defect.
- `scripts/odoosh_ssh.sh` — the §3c SSH recipe as a runnable script.
- `scripts/poll_module_version.py` — the §3f polling loop as a runnable script.
