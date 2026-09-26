# Dev Build Access

A `dev/*` build has no `admin/admin` and is not a fork of production — every push installs the
whole repository fresh, with demo data. This file has the exact calls; `SKILL.md` §3d has the
summary and the reasoning.

## 1. Sign in with Connect

Open the build card's **Connect** link. This signs the browser into that build's own database
with single sign-on — no credentials to look up. Use this whenever the task is a UI check (a
form, a button, a rendered report).

## 2. Set a throwaway password (needed only for RPC)

The Connect session has no password you can hand to `xmlrpc.client`. Set one yourself, once,
while the Connect-signed-in tab is open: open that tab's JS console and run

```js
await fetch('/web/dataset/call_kw', {
  method: 'POST', headers: {'Content-Type': 'application/json'}, credentials: 'same-origin',
  body: JSON.stringify({jsonrpc: '2.0', method: 'call', params: {
    model: 'res.users', method: 'write', args: [[2], {password: 'REPLACE-WITH-A-THROWAWAY-VALUE'}], kwargs: {}
  }})
}).then(r => r.json()).then(console.log)
```

`[[2]]` is `ik@dataegret.com`'s uid on every environment in this project (production, staging,
and every dev build alike) — confirm it if you are signed in as a different user. This call
rides the session cookie (`credentials: 'same-origin'`), which is why it must run from the
browser tab, not a standalone script. **Setting the password invalidates the current browser
session** — if you still need the UI afterward, sign in again through Connect (a fresh SSO pass
does not need the password you just set).

Pick a throwaway value you are not reusing anywhere else; it lives only for this build's
lifetime, and this build is disposable.

## 3. Connect over XML-RPC

```python
import xmlrpc.client

url = "https://dataegret-dev-<branch>-<build>.dev.odoo.com"  # exact host from the dashboard
db = "dataegret-dev-<branch>-<build>"                        # exact db name from the dashboard
login, password = "ik@dataegret.com", "REPLACE-WITH-THE-THROWAWAY-VALUE-YOU-JUST-SET"

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, login, password, {})
assert uid, "authenticate() returned falsy — wrong db name or password"
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
partners = models.execute_kw(db, uid, password, "res.partner", "search_read", [[]],
                              {"limit": 5, "fields": ["name"]})
```

Read both `url` and `db` from the dashboard for *this* build — they rotate on every rebuild and
are never safe to reuse from a previous session.

**Odoo 19 gotcha:** `create()` called with a list of value dicts returns a **list** of ids even
for a single record — `[139]`, not `139`. Index `[0]` or wrap the target id in a list before
using it as a many2one value, or the server raises a PostgreSQL array-type error.

## 4. What is and is not available here

- **Outgoing mail is caught by the platform** — nothing reaches a real inbox. This is what makes
  it safe to exercise a send path on a dev build.
- **There is no production data.** A dev build is a fresh install with demo data, never a fork of
  `prod` — for data resembling production, use a `staging_migration` rehearsal instead
  (`references/staging-and-production.md`).
- **Demo data exists, but only after the force-demo pass**, which runs *after* the full test
  suite. Anything that reads an "is this a demo database" flag sees it as false throughout
  install and the test run — never depend on demo-seeded rows in a test fixture; build fixtures
  explicitly in the test itself.
- **A build's own mail alias domain is empty until configured.** An inbound alias (a support
  address, a bounce handler) will not route real mail on a fresh dev build even though outgoing
  send paths work. Exercise alias-routed inbound behaviour directly instead (§6).

## 5. Run a cron once

A cron's private `_cron_*` method is not itself RPC-callable. Trigger the public wrapper instead:

```python
cron_ids = models.execute_kw(db, uid, password, "ir.cron", "search", [[("name", "=", "<exact cron name>")]])
models.execute_kw(db, uid, password, "ir.cron", "method_direct_trigger", [cron_ids])
```

## 6. Push an inbound message through the mail gateway

To exercise alias-routed or reply-routed inbound behaviour without waiting on real mail delivery
(which needs an alias domain you may not have, §4), feed a raw RFC 822 message straight into the
gateway:

```python
raw = open("sample.eml", "rb").read()
result = models.execute_kw(db, uid, password, "mail.thread", "message_process",
                            [False, xmlrpc.client.Binary(raw)])
```

The first argument is the fallback model to post to when no alias resolves the message — leave
it `False` to test real alias/reply routing, or name a model to force routing there. Pass the
message as `xmlrpc.client.Binary`; XML-RPC otherwise mangles raw bytes.

## 7. The three SSH timing/host-key traps, and the exact command

Covered in full in `references/traps.md`; the exact recipe (also wrapped in
`scripts/odoosh_ssh.sh` — prefer that over typing this by hand):

```
ssh -i ~/.ssh/odoosh_dataegret_rsa \
    -o IdentityAgent=none -o IdentitiesOnly=yes -o BatchMode=yes \
    -o ConnectTimeout=20 -o StrictHostKeyChecking=accept-new -o LogLevel=ERROR \
    -o UserKnownHostsFile="${TMPDIR:-/tmp}/odoosh-kh-<build-id>" \
    <build-id>@<build-domain> '<command>'
```

In one line each: (1) the platform answers port 22 under a throwaway host key before the
container exists, so a **per-build** known_hosts file is required — never the shared one; (2)
`sshd` may only start accepting connections after the test run has already finished, so an early
refusal proves nothing about build progress; (3) the gateway can refuse the registered key
outright, with no diagnosed cause, on the production container and — since 2026-09-21 — on some
dev containers too; when that happens, use the build's Shell tab or the branch's View errors
panel instead of retrying SSH indefinitely.
