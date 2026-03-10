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
| Claude settings | copies `config/claude-settings.json` → `~/.claude/settings.json` | automatic (skips if exists) |
| MCP config | templates `config/mcp.json` → `~/.claude/.mcp.json` | automatic (skips if exists) |
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
