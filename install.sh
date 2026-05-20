#!/usr/bin/env bash
# Claude Code environment setup — idempotent, safe to re-run
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
CLAUDE="$HOME/.claude"

echo "==> Claude environment setup from $REPO"

# ── 1. Agents symlink ────────────────────────────────────────────────────────
if [ -L "$CLAUDE/agents" ]; then
  echo "  agents symlink already exists — skipping"
elif [ -d "$CLAUDE/agents" ]; then
  echo "  WARNING: $CLAUDE/agents is a real directory, not a symlink."
  echo "  Move or delete it, then re-run."
else
  ln -s "$REPO/agents" "$CLAUDE/agents"
  echo "  created: $CLAUDE/agents -> $REPO/agents"
fi

# ── 1b. Skills symlink ───────────────────────────────────────────────────────
if [ -L "$CLAUDE/skills" ]; then
  echo "  skills symlink already exists — skipping"
elif [ -d "$CLAUDE/skills" ]; then
  echo "  WARNING: $CLAUDE/skills is a real directory, not a symlink."
  echo "  Move its contents into $REPO/skills/ and delete the directory, then re-run."
else
  ln -s "$REPO/skills" "$CLAUDE/skills"
  echo "  created: $CLAUDE/skills -> $REPO/skills"
fi

# ── 2. Claude settings ───────────────────────────────────────────────────────
SETTINGS_SRC="$REPO/config/claude-settings.json"
SETTINGS_DST="$CLAUDE/settings.json"
if [ -f "$SETTINGS_DST" ]; then
  echo "  $SETTINGS_DST already exists — skipping (edit manually if needed)"
else
  cp "$SETTINGS_SRC" "$SETTINGS_DST"
  echo "  created: $SETTINGS_DST"
fi

# ── 3. MCP config ────────────────────────────────────────────────────────────
MCP_SRC="$REPO/config/mcp.json"
MCP_DST="$CLAUDE/.mcp.json"
if [ -f "$MCP_DST" ]; then
  echo "  $MCP_DST already exists — skipping (edit manually if needed)"
else
  # Substitute $HOME with actual path so Claude can read it literally
  sed "s|\$HOME|$HOME|g" "$MCP_SRC" > "$MCP_DST"
  echo "  created: $MCP_DST"
  echo "  NOTE: Fill in WORDPRESS_USERNAME and WORDPRESS_PASSWORD in $MCP_DST"
fi

# ── 4. Project memory — de-website ──────────────────────────────────────────
MEMORY_DIR="$CLAUDE/projects/-Users-$(whoami)-work-de-website/memory"
MEMORY_SRC="$REPO/memory/de-website/MEMORY.md"
if [ -d "$MEMORY_DIR" ]; then
  echo "  project memory dir already exists — skipping"
else
  mkdir -p "$MEMORY_DIR"
  cp "$MEMORY_SRC" "$MEMORY_DIR/MEMORY.md"
  echo "  created: $MEMORY_DIR/MEMORY.md"
fi

# ── 5. Plugins (manual — require interactive approval) ───────────────────────
echo ""
echo "==> Plugins: run these commands to install (they require interactive approval):"
echo "    claude plugin install php-lsp"
echo "    claude plugin install frontend-design"
echo "    claude plugin install skill-creator"
echo "    claude plugin install playwright"

# ── 6. analytics-mcp (Python, via pipx) ─────────────────────────────────────
if command -v analytics-mcp &>/dev/null; then
  echo ""
  echo "  analytics-mcp already installed"
else
  echo ""
  echo "==> Installing analytics-mcp via pipx..."
  if command -v pipx &>/dev/null; then
    pipx install analytics-mcp
    echo "  installed analytics-mcp"
  else
    echo "  WARNING: pipx not found. Install it first: brew install pipx"
    echo "  Then run: pipx install analytics-mcp"
  fi
fi

# ── 7. Manual steps summary ──────────────────────────────────────────────────
cat <<'EOF'

==> Manual steps required:

  Google Analytics credentials (for analytics-mcp):
    gcloud auth application-default login
    (If gcloud is not installed: brew install --cask google-cloud-sdk)

  WordPress MCP credentials (for dataegret-staging):
    Edit ~/.claude/.mcp.json and fill in:
      WORDPRESS_USERNAME — your staging WP username
      WORDPRESS_PASSWORD — a WordPress Application Password
                          (WP Admin → Users → Edit → Application Passwords)

  SSH access (requires YubiKey):
    Add to ~/.ssh/config:
      Host de-staging
        HostName svc.pgco.me
        Port 50222
        User ik
      Host de-production
        HostName svc.pgco.me
        Port 50202
        User ik

  Project repo:
    mkdir -p ~/work/de/website
    cd ~/work/de/website
    git clone git@github.com:hydrobiont/de-website-3.git de-website-3
    cp de-website-3/.env.example de-website-3/.env
    # Edit .env with real license keys, then:
    docker compose -f de-website-3/docker-compose.yml up -d

EOF

echo "==> Done."
