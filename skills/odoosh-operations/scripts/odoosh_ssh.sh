#!/usr/bin/env bash
#
# odoosh_ssh.sh <build-id> <build-domain> [command]
#
# SSH into an odoo.sh build container for the dataegret project, using the
# documented agent-bypass recipe. Read references/dev-build-access.md and
# references/traps.md before relying on this: the gateway can refuse the
# registered key outright, sshd may not accept connections until the test
# run has finished, and a per-build known_hosts file is mandatory (the
# platform answers port 22 under a different host key before the container
# actually exists).
#
# Arguments:
#   <build-id>      the id shown on the odoo.sh build card — the SSH username.
#                   Read live from https://www.odoo.sh/project/dataegret ;
#                   it rotates on every rebuild, never reuse an old one.
#   <build-domain>  the build's .dev.odoo.com hostname, also read live from
#                   the dashboard.
#   [command]       a remote command to run non-interactively. Omit it for
#                   an interactive login shell.
#
# Exit status is the ssh exit status; 255 gets an explanatory message on
# stderr pointing at the dashboard fallback (View errors / Shell tab).

set -euo pipefail

if [ "$#" -lt 2 ]; then
  cat >&2 <<'USAGE'
Usage: odoosh_ssh.sh <build-id> <build-domain> [command]

  <build-id>      SSH username - the build id shown on the odoo.sh build card
                   (https://www.odoo.sh/project/dataegret). Read it live; it
                   rotates on every rebuild.
  <build-domain>  the build's *.dev.odoo.com hostname, also read live from
                   the dashboard.
  [command]       remote command to run non-interactively; omit for a login
                   shell.
USAGE
  exit 2
fi

BUILD_ID="$1"
BUILD_DOMAIN="$2"
shift 2
REMOTE_CMD=("$@")

KEY="${HOME}/.ssh/odoosh_dataegret_rsa"
KNOWN_HOSTS_DIR="${TMPDIR:-/tmp}"
KNOWN_HOSTS="${KNOWN_HOSTS_DIR%/}/odoosh-kh-${BUILD_ID}"

if [ ! -f "$KEY" ]; then
  echo "odoosh_ssh.sh: SSH key not found at ${KEY}" >&2
  echo "This is the dedicated odoo.sh SSH key, a separate thing from the" >&2
  echo "odoo-sh-dataegret-api keychain entry used for XML-RPC/JSON-RPC calls." >&2
  exit 2
fi

# Per-build throwaway known_hosts file: the platform answers port 22 under a
# host key that predates the actual container, so pinning it in the shared
# ~/.ssh/known_hosts would break verification for every later build.
: > "$KNOWN_HOSTS" 2>/dev/null || true

SSH_OPTS=(
  -i "$KEY"
  -o IdentityAgent=none
  -o IdentitiesOnly=yes
  -o BatchMode=yes
  -o ConnectTimeout=20
  -o StrictHostKeyChecking=accept-new
  -o LogLevel=ERROR
  -o UserKnownHostsFile="$KNOWN_HOSTS"
)

set +e
if [ "${#REMOTE_CMD[@]}" -eq 0 ]; then
  ssh "${SSH_OPTS[@]}" "${BUILD_ID}@${BUILD_DOMAIN}"
else
  ssh "${SSH_OPTS[@]}" "${BUILD_ID}@${BUILD_DOMAIN}" "${REMOTE_CMD[@]}"
fi
STATUS=$?
set -e

if [ "$STATUS" -eq 255 ]; then
  cat >&2 <<EOF

odoosh_ssh.sh: SSH did not complete (exit 255) against ${BUILD_ID}@${BUILD_DOMAIN}.

This is normally one of:
  - "Permission denied" - the gateway refused the registered key outright.
    Seen on the production container, and since 2026-09-21 on some dev
    containers too, with no diagnosed cause. It is not necessarily a sign
    the key or the command is wrong.
  - a timeout / connection refused - the build container may not be up yet,
    or sshd may not accept connections until the test run has already
    finished, even though the dashboard already shows the build as
    connected/finished.

Fallback, no SSH needed: open the branch page on
https://www.odoo.sh/project/dataegret , confirm the heading names the
branch you expect, then use its "View errors" panel (WARNING-and-above log
with tracebacks) or the build's own Shell tab (a browser-rendered terminal
that can grep/sed install.log and the enterprise source read-only).

Read references/traps.md in this skill for the three timing traps in full
before retrying.
EOF
fi

exit "$STATUS"
