---
name: browser-automation
description: >-
  How to drive a browser from ANY session on this machine: three global Playwright MCP servers —
  playwright-persistent (headless clone of the login vault; the default for small, unattended
  tasks), playwright-persistent-ui (the same logins in a visible window, for tasks the user
  watches, inspects visually, or must click through), playwright-isolated (clean headless
  profile for anonymous checks) — plus the browser-vault.sh commands for one-time logins, a
  mid-task UI handover, sync-back, status and cleanup. Load before dispatching browser-operator
  or touching any mcp__playwright-* tool: a web page must be clicked or filled, a login wall or
  cookie banner appears, a rendered page must be screenshotted or measured, GTM / GA4 / Search
  Console / wp-admin / odoo.sh / GitHub UI work comes up, a second browser identity is needed,
  or a "Browser is already in use" / profile-lock error shows up.
---

# Browser automation on this machine

## The three browsers (global, every session, every project)

| MCP server | Tools | Profile | Window | Use for |
|---|---|---|---|---|
| `playwright-persistent` | `mcp__playwright-persistent__browser_*` | per-session **clone of the login vault** | headless | **default**: small, unattended, logged-in tasks (read a report, toggle a setting, scrape, verify) |
| `playwright-persistent-ui` | `mcp__playwright-persistent-ui__browser_*` | its own clone of the same vault | visible | big or sensitive tasks the user wants to **watch**, visual inspection, anything where the user must **click** (2FA, confirm dialogs, CAPTCHAs, "does this look right?") |
| `playwright-isolated` | `mcp__playwright-isolated__browser_*` | in-memory, thrown away | headless | anonymous checks: cookie banners, tracking pixels, logged-out rendering, consent-mode measurements |

Every server starts on its own user-data-dir, so sessions and subagents never block each other
(Chromium's SingletonLock is per directory). The official plugin server `mcp__plugin_playwright_playwright__*`
uses a shared per-version profile and can still lock: do not use it. Never drive the user's own
Chrome (`mcp__Claude_in_Chrome__*`, `mcp__Control_Chrome__*`, `osascript`), never `screencapture`.

## Choosing, then delegating

1. **Small task, no user involvement expected** → `playwright-persistent` (headless). Dispatch
   `browser-operator` (sonnet; haiku for one exact read-only check) with the server named in the brief.
2. **The user wants to watch, inspect visually, or will have to click** → `playwright-persistent-ui`.
   Tell the user a window will open, dispatch `browser-operator` (sonnet) naming the UI server, and
   say in the brief that the user is at the keyboard and may act in the window (the agent then
   waits with `browser_wait_for` instead of stopping).
3. **What does an anonymous visitor see** → `playwright-isolated`.
4. Always put in the brief: the server, the vault identity expected (which Google/WordPress account),
   whether the user is present, and the hard "no destructive click without approval" list.

The session model plans and dispatches; it does not click through UIs itself when a subagent can.

## Logins

- **Durable (the normal way):** the user runs `~/.claude/bin/browser-vault.sh login <vault> "<url>"`.
  A window opens on the vault itself; they log in and close it. Every later session clone carries it.
- **Mid-task in headless mode (handover):** the agent reports `HANDOVER NEEDED`. The session then:
  1. makes sure that MCP session's browser is closed (`browser_close`, or the agent already did);
  2. tells the user what to do in the window;
  3. runs `~/.claude/bin/browser-vault.sh ui headless "<url>"` with `run_in_background` (it blocks
     until the user closes the window; never under a foreground timeout, a kill can lose the login);
  4. on the completion notification, re-invokes the agent — same clone, same cookies, now logged in;
  5. optionally persists it for future sessions: `~/.claude/bin/browser-vault.sh sync headless`
     (refuses while another process has the vault open; report that, do not force it).
- **In UI mode** no handover is needed: the user acts directly in the agent's window.
- Passwords, 2FA codes and CAPTCHAs never pass through an agent or a prompt.

## Identities

Vaults live in `~/.claude/chrome-profile/vaults/` (`default` → the legacy `~/.claude/chrome-profile/playwright`,
which carries two Chrome profiles: `Default` = ik@dataegret.com, `Profile 1` = connect@dataegret.com;
Chromium opens the last-used one, so the account chip must be checked on Google properties).
A second identity: `browser-vault.sh new <name>` then `login <name> <url>`. Which vault a session
gets is fixed at session start: `PLAYWRIGHT_VAULT=<name>` in the environment, else a line
`<name> <project-path-prefix>` in `~/.claude/chrome-profile/vaults.conf`, else `default`.

## Commands

```bash
~/.claude/bin/browser-vault.sh status                   # vaults, lock holders with ancestry, this session's clones (mode, browser open/closed)
~/.claude/bin/browser-vault.sh login default "<url>"    # one-time durable login on the vault (user)
~/.claude/bin/browser-vault.sh ui headless "<url>"      # handover: visible window on this session's headless clone
~/.claude/bin/browser-vault.sh sync headless            # persist that clone's logins into its vault
~/.claude/bin/browser-vault.sh probe default "<url>"    # headless smoke test: title + cookie count
~/.claude/bin/browser-vault.sh gc [--kill-orphans]      # drop dead clones; list/kill orphaned launchers on our dirs
~/.claude/bin/browser-vault.sh new <name>               # second identity
```

## Troubleshooting

- "Browser is already in use for …": a launcher bug now, not a wait. Run `status`, report its
  output, never kill another session's processes or delete `Singleton*` files.
- A site blocks headless Chromium (bot check, blank page): rerun the task on `playwright-persistent-ui`.
- MCP config changes (`~/.claude.json`, `mcpServers`) only affect new sessions.
- Launcher: `~/.claude/bin/playwright-mcp-session.sh` (clone + `npx @playwright/mcp`), library
  `browser-vault-lib.sh`, login/probe helper `browser-vault-launch.js` (uses the Playwright build
  bundled with the cached `@playwright/mcp`, so vaults stay byte-compatible). Log:
  `~/.claude/chrome-profile/sessions.log`.
