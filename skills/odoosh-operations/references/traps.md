# Traps

Full, dated detail. `SKILL.md` and the other reference files summarise the traps relevant to their own recipe;
this file is the complete catalogue — read it whenever a result looks surprising, before reporting it as a
defect or a regression.

### 2026-09-09 — A dashboard URL for a slash-named branch can silently render production

A URL built from a branch name containing a slash (`dev/my-feature`) does not reliably address that branch.
The plain path falls through to production's own build history, and even a URL-encoded slash (`%2F`) that
worked on one date failed on a later one — the application rewrote the address back to its unencoded form and
served production again. The only reliable confirmation of which branch a dashboard page is showing is the
page's own heading, which prints the branch name; the reliable way to navigate there is the sidebar's branch
list, not a constructed URL. This matters beyond cosmetics: the same page carries the Rebuild and Merge
controls, both of which act on whichever branch the page is actually showing.

### 2026-09-09 — odoo.sh runs the whole test suite before loading demo data

A `dev/*` build installs every module with the full test suite enabled first, and only afterward runs a
separate force-demo pass that actually loads demo records. On a build observed in full, the force-demo pass
ran after the tests had already finished. Any code that checks whether it is running against a demo database
reads that check as false throughout both install and the entire test run, even though the finished database
reports demo modules as loaded afterward. Never gate install-time seeding on a demo-database flag, and never
let a test fixture depend on rows an install hook created for that reason — build fixtures explicitly in the
test's own setup.

### 2026-07-27 — `noupdate` decides whether an operational lever survives an update

A record loaded from a module's own data file is reset to that file's value on every module update unless it,
or its enclosing block, carries `noupdate="1"`. The sharpest case: a cron that ships disabled by design and is
then enabled by hand in production gets switched back off by the very next update, with no error anywhere.
Wrap any record an operator is expected to tune after go-live — a cron's active flag, a live parameter — in
`noupdate="1"`, with a comment naming it as the lever, and confirm empirically after a real update that the
flag survived rather than trusting the XML attribute alone. Ordinary database rows (`ir.config_parameter`
values, user-created records, a module's own cache fields) are not subject to this at all and survive updates
regardless; what does get re-applied on every update is view architecture, menus, ACL rows, and `ir.rule`
domains, along with any data record not marked `noupdate`.

### 2026-07-27 — Five ways a green test suite can prove nothing

1. **Context propagation through a recordset.** A fixture created with a suppression flag
   (`with_context(some_no_confirm=True).create(...)`) carries that flag into every later `write()`/`unlink()`
   on the returned recordset, silently disabling the behaviour a later part of the same test means to exercise
   — and the test still passes, because it asserts against a baseline of zero rather than the effect it meant
   to trigger. Scope such flags to the single call that needs them and drop them from whatever recordset the
   test hands back for further use.
2. **Precommit semantics.** `mail.tracking.value` rows (field-change history behind the chatter) materialize
   in a precommit hook a standard, rolled-back test transaction never reaches — `flush_all()` alone leaves
   zero rows, and a record created and written to within the same precommit window gets no field tracking
   recorded at all. Assert only after `flush_all()` and `env.cr.precommit.run()`. Production is unaffected,
   because every real HTTP request commits.
3. **Odoo sends real mail during fixture setup.** Ordinary behaviour (for example, assigning an activity)
   sends a notification email as a side effect, independent of the feature under test. Baseline a no-mail
   guard after fixtures finish, not before — a guard set too early fails for a reason unrelated to the code
   being tested.
4. **Accounting fixtures.** A bare test database has no chart of accounts and no journals; a test that posts
   or reads accounting entries needs `AccountTestInvoicingCommon`, and some accounting-dependent assertions
   additionally need the `post_install` tag to run only once the full module set has finished loading.
5. **`active_test` hides archived rows.** A plain `search`/`search_count` domain silently excludes archived
   records on any model with an `active` field — a count of "how many reminders exist" once read 2 when 3
   existed, one of them paused. Any assertion about existence or count needs `("active", "in", [True, False])`
   or `context={"active_test": False}`; a paused record hidden this way is otherwise indistinguishable from a
   deleted one.

### 2026-08-04 — A Cloudflare WAF in front of one hostname produces false reds

Production answers on two hostnames: `dataegret.odoo.com`, direct to odoo.sh with no proxy, and
`odoo.dataegret.com`, Cloudflare-proxied in front of the same database (kept because `web.base.url` is pinned
to it, so every invite and password-reset link routes through it). A Cloudflare block on the proxied hostname
returns HTTP 403 with a block page before the request reaches Odoo — nothing appears in any odoo.sh log, so a
check against that hostname can read as a broken feature that was never actually exercised. Probe
`dataegret.odoo.com` to bypass the WAF when testing Odoo behaviour; when a check must use the proxied
hostname, read the response's `server:` header before concluding anything (`cloudflare` means the edge
answered, `Odoo.sh` means the origin did). A Cloudflare block page names the zone's apex domain regardless of
which subdomain was actually requested, so a block on the Odoo hostname can look like the company website
itself is blocked — it is not. This WAF sits entirely outside the addons repository and outside Odoo: neither
a module update nor a repository rollback resets it. Cloudflare's own Security Events log, which explains a
block, retains only 24 hours on this plan — pull it the same day.

### 2026-07-27 — `Test: Warning` is the healthy badge for this project's modules

A healthy build here shows `Test: Warning` with sub-status `done` — several install-time warnings are expected
— while `Test: Success` is not a "more passing" result, merely one that happened to log nothing at that level.
A badge reading `Test: Failed` can co-list a module with no actual failing test anywhere in the log (full
evidence and the fix pattern in `references/dashboard-and-logs.md`). Never call a build green or red from the
card colour alone; read `install.log`.

### 2026-09-21 — The SSH gateway can refuse the registered key outright, and three timing traps compound the confusion

The documented recipe needs `-o IdentityAgent=none -o IdentitiesOnly=yes` on a machine where the local
ssh-agent offers a YubiKey PIV key before the registered RSA key gets a turn — otherwise the connection fails
on "agent refused operation" before the right key is even tried, even though that key needs no passphrase and
the exchange is otherwise non-interactive. Layered on top: the platform answers port 22 under a throwaway host
key before the build container exists, so a per-build `UserKnownHostsFile` is required — pinning an early
wrong key in the shared `~/.ssh/known_hosts` breaks host verification for every later build; `sshd` can start
accepting connections only after the test run has already finished, so a refused connection early on says
nothing about whether the build is done; and a build can show as connected/finished on the dashboard while
still refusing every connection for several minutes. As of 2026-09-21, three separate dev builds refused the
registered key outright with no diagnosed cause — not every refusal is one of the timing traps above. When SSH
will not cooperate, fall back to the branch page's View errors button or the build's own Shell tab.

### 2026-09-21 — The odoo.sh build id lives only on the dashboard, and the browser profile can be locked by another session

There are no GitHub commit statuses or check runs on the addons repository, and no branch-name-derived
hostname resolves reliably for a build that is not the currently live one — the build id (the SSH username)
must be read from the dashboard each time. The persistent browser profile used to reach it can be locked by
another session (a `SingletonLock` file names the holding process); a browser-automation agent correctly
refuses to kill a foreign process or silently fall back to an isolated profile, so check the lock before
retrying a failed navigation in a loop, and ask the user to release the session if another one holds it.

### The database's own log table is not a log source here

odoo.sh does not populate `ir.logging` for these builds — querying it over RPC reads empty even while the
container is actively logging. This is the same finding that established `install.log`, read over SSH or the
Shell tab, as the authoritative record in the first place (2026-07-27): there is no database-side shortcut to
a build's log output, only the container's own log files.
