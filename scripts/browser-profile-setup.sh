#!/usr/bin/env bash
# Launch the persistent Chromium profile used by the browser-operator agent,
# so the user can log into a site once and have the cookies saved for future
# agent runs.
#
# Usage:
#   ./scripts/browser-profile-setup.sh                       # opens about:blank
#   ./scripts/browser-profile-setup.sh https://example.com/login
#
# Close the browser window when done — Playwright writes the profile to disk
# on clean shutdown.

set -euo pipefail

PROFILE_DIR="${HOME}/.claude/chrome-profile/playwright"
START_URL="${1:-about:blank}"

mkdir -p "$PROFILE_DIR"

echo "==> Browser profile: $PROFILE_DIR"
echo "==> Opening:         $START_URL"
echo ""
echo "    A Chromium window will appear. Log into the site(s) you need."
echo "    Close the window when done — cookies will be saved to the profile."
echo ""

# Use the Playwright-bundled Chromium so the profile is byte-compatible
# with what the MCP server uses at runtime.
#
# npx will install @playwright/test on first use; subsequent runs are cached.
npx --yes -p @playwright/test@latest playwright open \
  --browser=chromium \
  --user-data-dir="$PROFILE_DIR" \
  "$START_URL"

echo ""
echo "==> Profile saved. The browser-operator agent will reuse this session."
