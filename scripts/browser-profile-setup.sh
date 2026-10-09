#!/usr/bin/env bash
# Superseded on 2026-09-26 by ~/.claude/bin/browser-vault.sh (login vault + per-session clones).
# Kept so older instructions keep working: opens the DEFAULT vault for a one-time login.
exec "${HOME}/.claude/bin/browser-vault.sh" login default "${1:-about:blank}"
