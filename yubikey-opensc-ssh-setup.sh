#!/usr/bin/env bash
#
# yubikey-opensc-ssh-setup.sh
#
# Configure macOS so SSH uses the YubiKey's OpenPGP *authentication* subkey
# (the RSA key already in your servers' authorized_keys) under a modern,
# host-bound OpenSSH client — without gpg-agent (which can't do host-bound)
# and without re-deploying any public key.
#
# What it sets up:
#   1. Homebrew openssh + opensc (Apple's ssh-agent rejects PKCS#11 providers)
#   2. OpenSC -> OpenPGP applet (so it exposes the RSA auth key, not PIV)
#   3. OPENSC_CONF exported so that config is used
#   4. scdaemon shares the card (disable-ccid + pcsc-shared) so gpg + OpenSC coexist
#   5. ~/.ssh/config Host * : PKCS11Provider + IdentityAgent none
#        - PKCS11Provider: ssh loads the card directly and signs in-process,
#          so host-bound is satisfied
#        - IdentityAgent none: ignore gpg-agent so its copy of the key can't
#          shadow the connection and fail host-bound
#
# It does NOT touch any PIN or anything on the card itself — the card is the
# same physical device; only this host's client config changes.
#
# Idempotent: safe to re-run. Open a NEW terminal afterward.

set -euo pipefail

note() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mWARN:\033[0m %s\n' "$*"; }

# --- 1. Prerequisites ------------------------------------------------------
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew not found. Install it from https://brew.sh and re-run." >&2
  exit 1
fi
BREW_PREFIX="$(brew --prefix)"

for pkg in openssh opensc; do
  if brew list --formula "$pkg" >/dev/null 2>&1; then
    note "$pkg already installed"
  else
    note "Installing $pkg"
    brew install "$pkg"
  fi
done

# --- 1b. Verify the installed software -------------------------------------
# Pin the Homebrew binaries explicitly (Apple's /usr/bin builds won't do).
SSH_BIN="$BREW_PREFIX/bin/ssh"
SSHKEYGEN_BIN="$BREW_PREFIX/bin/ssh-keygen"
OPENSC_TOOL="$BREW_PREFIX/bin/opensc-tool"
PKCS11_TOOL="$BREW_PREFIX/bin/pkcs11-tool"

[ -x "$SSH_BIN" ]       || { echo "Missing $SSH_BIN (brew openssh not linked?)" >&2; exit 1; }
[ -x "$SSHKEYGEN_BIN" ] || { echo "Missing $SSHKEYGEN_BIN" >&2; exit 1; }

# OpenSSH: print version and require >= 8.9 (host-bound public-key auth).
SSH_VER_STR="$("$SSH_BIN" -V 2>&1)"
SSH_VER="$(printf '%s' "$SSH_VER_STR" | sed -n 's/^OpenSSH_\([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p')"
note "OpenSSH at $SSH_BIN -> $SSH_VER_STR"
if [ -n "$SSH_VER" ]; then
  ssh_major="${SSH_VER%%.*}"; ssh_minor="${SSH_VER##*.}"
  if [ "$ssh_major" -lt 8 ] || { [ "$ssh_major" -eq 8 ] && [ "$ssh_minor" -lt 9 ]; }; then
    warn "OpenSSH $SSH_VER is older than 8.9 — run 'brew upgrade openssh'."
  fi
else
  warn "Could not parse OpenSSH version from: $SSH_VER_STR"
fi

# OpenSC: print version.
if [ -x "$OPENSC_TOOL" ]; then
  note "OpenSC at $OPENSC_TOOL -> $("$OPENSC_TOOL" --version 2>&1 | head -1)"
else
  warn "opensc-tool not found at $OPENSC_TOOL (opensc install may be incomplete)."
fi

# --- 2. Locate the OpenSC PKCS#11 module -----------------------------------
MOD=""
for cand in "$BREW_PREFIX/lib/opensc-pkcs11.so" "$BREW_PREFIX/lib/pkcs11/opensc-pkcs11.so"; do
  [ -e "$cand" ] && MOD="$cand" && break
done
[ -z "$MOD" ] && MOD="$(find "$BREW_PREFIX" -name 'opensc-pkcs11.so' 2>/dev/null | head -1 || true)"
if [ -z "$MOD" ]; then
  echo "Could not find opensc-pkcs11.so under $BREW_PREFIX" >&2
  exit 1
fi
note "OpenSC module: $MOD"

# Verify the module actually loads as a PKCS#11 library.
if [ -x "$PKCS11_TOOL" ]; then
  if "$PKCS11_TOOL" --module "$MOD" --show-info >/dev/null 2>&1; then
    note "PKCS#11 module initialises OK"
  else
    warn "pkcs11-tool could not initialise $MOD — continuing, but verify the OpenSC install."
  fi
fi

# --- 3. OpenSC: prefer the OpenPGP applet ----------------------------------
mkdir -p "$HOME/.config/opensc"
OPENSC_CONF_FILE="$HOME/.config/opensc/opensc.conf"
if grep -q 'card_drivers *= *openpgp' "$OPENSC_CONF_FILE" 2>/dev/null; then
  note "opensc.conf already prefers the OpenPGP applet"
else
  note "Writing $OPENSC_CONF_FILE (prefer OpenPGP applet over PIV)"
  cat > "$OPENSC_CONF_FILE" <<'EOF'
app default {
    card_drivers = openpgp, internal;
}
EOF
fi

# --- 4. Export OPENSC_CONF persistently (zsh) ------------------------------
ZSHENV="$HOME/.zshenv"
if grep -rqs 'OPENSC_CONF' "$HOME/.zshenv" "$HOME/.zshrc" "$HOME/.zprofile" 2>/dev/null; then
  note "OPENSC_CONF already exported in a zsh startup file"
else
  note "Adding OPENSC_CONF export to $ZSHENV"
  printf '\n# OpenSC: use the OpenPGP applet for SSH (YubiKey)\nexport OPENSC_CONF="$HOME/.config/opensc/opensc.conf"\n' >> "$ZSHENV"
fi

# --- 5. scdaemon: share the card with OpenSC -------------------------------
mkdir -p "$HOME/.gnupg"; chmod 700 "$HOME/.gnupg"
SCD="$HOME/.gnupg/scdaemon.conf"
for opt in disable-ccid pcsc-shared; do
  if grep -qx "$opt" "$SCD" 2>/dev/null; then
    note "scdaemon.conf already has '$opt'"
  else
    note "Adding '$opt' to $SCD"
    echo "$opt" >> "$SCD"
  fi
done

# --- 6. ssh config: offer the card key to all hosts, ignore the agent ------
mkdir -p "$HOME/.ssh"; chmod 700 "$HOME/.ssh"
SSHCONF="$HOME/.ssh/config"
touch "$SSHCONF"; chmod 600 "$SSHCONF"
MARKER='# >>> yubikey-opensc-ssh >>>'
if grep -qF "$MARKER" "$SSHCONF"; then
  note "ssh config already has the YubiKey block (leaving as-is)"
else
  note "Appending Host * block to $SSHCONF"
  cat >> "$SSHCONF" <<EOF

$MARKER
# Use the YubiKey OpenPGP auth key via OpenSC for every host.
# PKCS11Provider: ssh signs in-process -> host-bound works.
# IdentityAgent none: ignore gpg-agent so its non-host-bound copy can't shadow.
Host *
    PKCS11Provider $MOD
    IdentityAgent none
# <<< yubikey-opensc-ssh <<<
EOF
fi

# --- 7. Reload gpg daemons so scdaemon picks up the new options ------------
note "Restarting gpg agents"
gpgconf --kill all >/dev/null 2>&1 || true

# --- 8. Sanity checks ------------------------------------------------------
# 8a. Make sure plain `ssh` resolves to the Homebrew build.
SSH_PATH="$(command -v ssh || true)"
if [ "$SSH_PATH" = "$SSH_BIN" ]; then
  note "'ssh' on PATH resolves to the Homebrew build ($SSH_PATH)"
else
  warn "'ssh' resolves to '$SSH_PATH', not '$SSH_BIN'."
  warn "Apple's /usr/bin/ssh may refuse to load the PKCS#11 module in-process."
  warn "Put '$BREW_PREFIX/bin' ahead of /usr/bin in your PATH (e.g. in ~/.zshenv)."
fi

# 8b. Functional check: if the YubiKey is present, confirm OpenSC exposes the
#     OpenPGP RSA key (proves the applet selection + module path are correct).
TMP_PUB="$(mktemp)"
if OPENSC_CONF="$OPENSC_CONF_FILE" "$SSHKEYGEN_BIN" -D "$MOD" >"$TMP_PUB" 2>/dev/null && [ -s "$TMP_PUB" ]; then
  if grep -q '^ssh-rsa ' "$TMP_PUB"; then
    note "Card check: OpenSC exposes the OpenPGP RSA key(s):"
    "$SSHKEYGEN_BIN" -lf "$TMP_PUB" 2>/dev/null | sed 's/^/        /'
  else
    warn "Card check: keys returned but none are RSA — OpenSC may be on the PIV applet."
    warn "Confirm $OPENSC_CONF_FILE contains 'card_drivers = openpgp, internal;'."
  fi
else
  note "Card check skipped (YubiKey not detected or card busy) — insert it and test with ssh."
fi
rm -f "$TMP_PUB"

note "Done."
echo
echo "Next steps:"
echo "  1. Open a NEW terminal (so OPENSC_CONF is exported)."
echo "  2. Insert the YubiKey."
echo "  3. Test:   ssh -vvv <user>@<host>"
echo "     Expect: 'Offering public key: Authentication key RSA ... token',"
echo "             a PIN prompt, a touch (key blinks), then a shell."
echo
echo "If a connection ever fails with a card/login error, it's transient"
echo "contention — run 'gpgconf --kill scdaemon' and retry."
