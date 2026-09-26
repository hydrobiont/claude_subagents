# Staging and Production

## Push versus Rebuild

A `git push` to `staging_migration` updates that branch's **existing**
database in place: odoo.sh runs a module update only on whichever modules
changed their manifest version, exactly like a push to any other branch.
Nothing is re-forked, so whatever state you built up in a previous
rehearsal — records you created, parameters you retargeted — survives.

**Rebuild** discards that database and re-forks a fresh copy of current
production. Use it only when the rehearsal specifically needs a clean
production snapshot; reserve it, because:

- **It does not auto-install any module that only a previous session
  installed by hand** but that has not yet reached production — a Rebuild
  can silently revert what looks like a regression when it is really just
  an un-repeated manual step from before.
- **It decapitates the Slack support bot.** The bot's `ODOO_URL` is pinned
  and its HMAC secret is generated per-fork; re-forking restores the old
  pin and loses the secret, and the only symptom is a routine-looking
  5-minute WARNING in the log — nothing that reads as an outage. Confirm
  whether anyone depends on the bot on this environment before you
  Rebuild, and if you do, plan to re-point `ODOO_URL` and regenerate the
  secret afterward.

`dev/*` builds are unaffected by any of this — every push there always
rebuilds from scratch with demo data, by design
(`references/dev-build-access.md`).

## What auto-updates and what needs an explicit install

A push (to any branch) reloads a module's code and data **only when its
manifest `version` field changed** since the currently-running version. A
code-only push against an unchanged version ships the files to the
container, but the running database never reloads them.

A **brand-new** module — one this branch's database has never had
installed — is never auto-installed by either a push or a Rebuild. It
needs an explicit `-u`/install action once (by hand through the Apps UI, or
from a data file that names it), after which its later version bumps ride
the ordinary update mechanism like any other module.

## The production update sequence, with timings

1. Get the user's explicit go for this specific change — a standing
   authorisation covers the change it was given for, not the next one.
2. `git push origin <sha>:prod` — a fast-forward push of an already-tested
   commit. This is a deploy, not a rehearsal; do it once you have a green
   result from `SKILL.md` §3b (and, if the change touches existing data or
   the UI, a staging rehearsal).
3. odoo.sh restarts the production build to load the new version. Expect
   roughly a 30-second window of HTTP 503 on the production URL during
   that restart — normal, not a failed deploy.
4. Poll `installed_version` on `ir.module.module` over XML-RPC until it
   reads the new value — `scripts/poll_module_version.py` does this,
   tolerating the 503 window and ordinary connection errors rather than
   treating the first failed poll as a failed deploy. A successful `git
   push` is not itself evidence the update landed; the version readback
   is.
5. Verify, read-only, against the now-confirmed database (checklist
   below).
6. Fast-forward the shared local checkout: `git -C ~/work/de/odoo/odoo
   pull --ff-only` — so the next session's view of `prod` reflects what is
   actually running rather than a stale local branch.

**The manifest version bump is mandatory on every shipped change, not a
formality some changes can skip.** Forget it and the code and data files
reach the container, but the database keeps running the old version with
nothing to flag it. The same bump is what makes a JS asset bundle
regenerate — a JS-only fix with no version bump looks, after deploy,
exactly like a change that never happened.

**Any operational lever the change ships — a cron's `active` flag, a
tunable parameter, an alias — belongs in a `noupdate="1"` data block.**
Without it, the very next module update (this one or a future one) resets
that record to the value shipped in the file, silently, with no error.
This project has seen a live cron switched back off this way. Records you
want re-applied on every update (views, menus, ACL rows, `ir.rule`
domains, a module's own record definitions) stay outside `noupdate` — the
rule only protects records an operator is expected to tune after go-live.

## Post-deploy verification checklist

Confirm all of these, live, before calling the deploy done — a successful
version readback proves the update ran, not that it did what you intended:

- `installed_version` on `ir.module.module` matches the new manifest
  version, read over XML-RPC.
- Fields and views actually load — read the live `ir.ui.view.arch_db` for
  any view you shipped or changed, not just that the model responds.
- The data records the change shipped are present (params, menu items,
  security rules).
- Cron `active` flags and intervals read as intended, especially any cron
  the change touched.
- Guards are unchanged: `noupdate` levers survived, `mail.mail` and
  `mail.notification` counts have not moved against anyone real, and any
  access-control assumption the change depends on still holds.

## The shared-checkout fast-forward

The addons checkout at `~/work/de/odoo/odoo` is shared across sessions.
After a production push lands, fast-forward it (`git -C ~/work/de/odoo/odoo
pull --ff-only`) so a later session's view of `prod` is not stale — never
force-push or rebase this checkout's branches to make it agree; fast-forward
only, and if it cannot fast-forward, stop and report rather than forcing
it.
