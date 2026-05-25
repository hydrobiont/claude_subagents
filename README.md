# claude_subagents

Configuration and agents for Claude Code, synced across machines via this repo.

## Quick setup on a new machine

```bash
git clone https://github.com/hydrobiont/claude_subagents.git ~/claude_subagents
cd ~/claude_subagents
./install.sh
```

Then follow the manual steps printed at the end.

---

## What's in this repo

```
agents/          Custom sub-agents (linked into ~/.claude/agents)
                   browser-operator    Browser automation via a dedicated, persistent Chromium profile
skills/          Custom skills (linked into ~/.claude/skills)
                   technical-writer/   dba-docs-internal + trainings2025 writer
scripts/
  browser-profile-setup.sh  Bootstrap helper — opens the persistent Chromium profile
                            so the user can log into a site once and reuse cookies forever
config/
  claude-settings.json   ~/.claude/settings.json — plugins + settings
  mcp.json               ~/.claude/.mcp.json template — MCP server definitions
memory/
  de-website/
    MEMORY.md    Project memory for dataegret.com website work
install.sh       Idempotent setup script
```

---

## What `install.sh` does

| Step | What | Where |
|---|---|---|
| Agents symlink | `~/.claude/agents → ~/claude_subagents/agents` | automatic |
| Skills symlink | `~/.claude/skills → ~/claude_subagents/skills` | automatic |
| Claude settings | copies `config/claude-settings.json` → `~/.claude/settings.json` | automatic (skips if exists) |
| MCP config | merges `config/mcp.json` into `~/.claude/.mcp.json` (adds new servers, never overwrites existing) | automatic |
| Browser profile dir | creates `~/.claude/chrome-profile/playwright/` (empty) | automatic |
| Project memory | copies `memory/de-website/MEMORY.md` into `~/.claude/projects/` | automatic (skips if exists) |
| analytics-mcp | `pipx install analytics-mcp` | automatic if pipx available |
| Plugins | prints `claude plugin install` commands | **manual** (require interactive approval) |

---

## MCP servers

### memory
Global conversation memory across sessions.
- Package: `@modelcontextprotocol/server-memory` (npx)
- No credentials needed.

### analytics
Google Analytics 4 read access (run reports, get property details, etc.).
- Package: `analytics-mcp` (Python, installed via pipx)
- Auth: Google Application Default Credentials

```bash
# Install gcloud if needed
brew install --cask google-cloud-sdk

# Authenticate (opens browser)
gcloud auth application-default login
```

### dataegret-staging
WordPress REST API access to dev2.dataegret.com.
- Package: `@instawp/mcp-wp` (npx)
- Credentials: fill in `~/.claude/.mcp.json` after running install.sh

```
WORDPRESS_USERNAME  — your staging WP username
WORDPRESS_PASSWORD  — WordPress Application Password
                      (WP Admin → Users → Edit user → Application Passwords)
```

### playwright-persistent
Playwright MCP server backed by a **dedicated, persistent Chromium profile** at
`~/.claude/chrome-profile/playwright/`. Used exclusively by the `browser-operator`
sub-agent. Survives restarts, isolated from your daily Chrome, never collides with
the user's own browser sessions.

- Package: `@playwright/mcp@latest` (npx, with `--user-data-dir`)
- No credentials in config — logins are per-site, stored in the profile cookies.

To log into a site for the first time:

```bash
~/claude_subagents/scripts/browser-profile-setup.sh https://dataegret.com/wp-admin/
# A Chromium window opens, you log in, you close it → cookies saved.
# Next agent invocation reuses the session.
```

Distinct from the official `playwright` plugin MCP (which uses an ephemeral
profile with no saved logins). The browser-operator agent always uses
`playwright-persistent`, never the ephemeral one.

---

## The `browser-operator` sub-agent

A general-purpose browser automation agent, available from any project on any
machine that has run `install.sh`. Drives the persistent Chromium profile above,
so it never asks the user to grant Chrome extension permissions or log into sites
twice.

Invoke it from any session for web-UI tasks that cannot be done via API:

```
Agent({
  subagent_type: "browser-operator",
  prompt: "Set the Yoast 'noindex' flag on https://dataegret.com/wp-admin/post.php?post=1196&action=edit
           (this is the 'Sorry to see you go!' page). Verify the front-end
           https://dataegret.com/news-blog/sorry-to-see-you-go/ shows
           'noindex, follow' in the robots meta tag after saving."
})
```

The agent uses the persistent Chromium profile, snapshots the page to orient,
performs the action, and verifies the change via both the admin UI and a
`curl` of the front-end. If a login is missing, it stops and tells you which
URL to run through `browser-profile-setup.sh`.

---

## Plugins

Install interactively after running `install.sh`:

```bash
claude plugin install php-lsp
claude plugin install frontend-design
claude plugin install skill-creator
claude plugin install playwright
```

---

## SSH access (dataegret servers, requires YubiKey)

Add to `~/.ssh/config`:

```
Host de-staging
  HostName svc.pgco.me
  Port 50222
  User ik

Host de-production
  HostName svc.pgco.me
  Port 50202
  User ik
```

Then test: `ssh de-staging`
Touch YubiKey when prompted.

---

## Project repo (dataegret.com website)

```bash
mkdir -p ~/work/de/website
cd ~/work/de/website
git clone git@github.com:hydrobiont/de-website-3.git de-website-3
cp de-website-3/.env.example de-website-3/.env
# Edit .env: add real Elementor Pro and ACF Pro license keys
docker compose -f de-website-3/docker-compose.yml up -d
```

Local dev runs at http://localhost:8080.

---

## Keeping memory in sync

The `memory/de-website/MEMORY.md` file is the source of truth for project context.
After significant work sessions, copy the updated memory back to the repo:

```bash
cp ~/.claude/projects/-Users-$(whoami)-work-de-website/memory/MEMORY.md \
   ~/claude_subagents/memory/de-website/MEMORY.md
git add memory/de-website/MEMORY.md
git commit -m "Update de-website project memory"
git push
```

On the other machine, pull and reinstall memory:

```bash
git pull
cp ~/claude_subagents/memory/de-website/MEMORY.md \
   ~/.claude/projects/-Users-$(whoami)-work-de-website/memory/MEMORY.md
```
