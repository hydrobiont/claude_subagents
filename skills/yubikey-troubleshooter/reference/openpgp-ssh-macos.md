# OpenPGP-card SSH key on modern macOS (host-bound) — the full playbook

This is the hard-won procedure for: **"my YubiKey's OpenPGP authentication
subkey is in every server's `authorized_keys`, and SSH suddenly broke."** It
almost always breaks because the OpenSSH client got upgraded to a version
(8.9+, and aggressively in 10.x) that negotiates **host-bound** public-key auth
(`publickey-hostbound`), which **gpg-agent cannot satisfy** (it doesn't
implement `session-bind@openssh.com`). gpg-agent was the thing serving the
`cardno:` key, so every connection now dies at `agent refused operation`.

The goal is to keep using that exact RSA key with **no public-key redeploy** to
any server.

## The one-line mental model

Serve the OpenPGP auth key to SSH **without gpg-agent**: load OpenSC's PKCS#11
module *directly into the ssh client* (`PKCS11Provider` / `ssh -I`). ssh then
signs **in-process**, so it does host-bound itself and never needs the agent.

## Why each obvious path fails (so you don't waste time)

- **gpg-agent** — no `session-bind`; refuses host-bound. The original breakage.
- **ssh-agent + `ssh-add -s opensc`** — Apple's `/usr/bin/ssh-agent` refuses
  external PKCS#11 providers outright; even Homebrew's agent is defeated by the
  `-P` provider whitelist matching the *resolved* Homebrew Cellar realpath, and
  on some setups by a persistent agent that keeps relocating `SSH_AUTH_SOCK`
  into `~/.ssh/agent/`. Don't fight the agent — go agentless with `-I`.
- **OpenSC default applet** — on a YubiKey with both applets, OpenSC defaults
  to **PIV** (exposes the wrong, ECCP384 slot-9D key). You must force the
  OpenPGP driver.
- **macOS PIV-native route** — clean, but uses the PIV key (different public
  key) → would require redeploying to servers. Rejected when "no redeploy".

## The working configuration (what to set, and why)

1. **Use Homebrew's OpenSSH and OpenSC**, not Apple's.
   `brew install openssh opensc`. Apple's `ssh-agent`/library-validation reject
   the third-party module; Homebrew's client loads it in-process fine. Make
   sure `ssh` resolves to `$(brew --prefix)/bin/ssh` (PATH order).

2. **Point OpenSC at the OpenPGP applet** so it exposes the RSA auth key, not
   PIV. In `~/.config/opensc/opensc.conf`:
   ```
   app default {
       card_drivers = openpgp, internal;
   }
   ```
   and export `OPENSC_CONF="$HOME/.config/opensc/opensc.conf"` (in `~/.zshenv`)
   so it's actually used. Verify: `ssh-keygen -D <module>` should print an
   `ssh-rsa` key whose fingerprint matches the deployed key — not an ECDSA one.

3. **Let gpg and OpenSC share the card.** gpg's scdaemon grabs the YubiKey's
   CCID exclusively and locks OpenSC out (`provider ... returned no slots`, or
   `PKCS#11 login failed: error 48` = CKR_DEVICE_ERROR). In
   `~/.gnupg/scdaemon.conf`:
   ```
   disable-ccid
   pcsc-shared
   ```
   `disable-ccid` makes scdaemon use PC/SC; `pcsc-shared` opens the card in
   shared mode so both can read it. `gpgconf --kill all` to reload.

4. **ssh config — offer the card key everywhere, ignore the agent.** In
   `~/.ssh/config`:
   ```
   Host *
       PKCS11Provider /opt/homebrew/lib/opensc-pkcs11.so
       IdentityAgent none
   ```
   - `PKCS11Provider`: ssh loads the card itself and signs in-process → host-bound OK.
   - `IdentityAgent none`: ignore gpg-agent entirely, so its non-host-bound
     copy of the same key can't be offered first and shadow the connection.
   - **Do NOT use `IdentitiesOnly yes` for this** — counterintuitively it also
     filters out the `PKCS11Provider` keys (only default IdentityFiles survive),
     so the card key never gets offered. `IdentityAgent none` is the correct
     lever; it drops the agent without dropping the provider.

## Verifying success in `ssh -vvv`

Good run shows, in order:
```
provider .../opensc-pkcs11.so slot 0: label <OpenPGP card (User PIN)>
pkcs11_fetch_keys: ... RSA SHA256:<your deployed fp>
...
Offering public key: Authentication key RSA SHA256:<your fp> token
Server accepts key: ... token
get_agent_identities: bound agent to hostkey      # host-bound satisfied
```
then a PIN prompt and a touch (if UIF Auth=on), then a shell.

## The PIN trap (this bites hard)

If the **wrong** PIN is entered to OpenSC repeatedly, PW1 silently decrements
and **locks** — surfacing as `error 48` (CKR_DEVICE_ERROR, easy to misread as
contention) then `PIN locked` (CKR_PIN_LOCKED 0xa4). Before burning attempts
through interactive ssh:

1. Set a known PW1 via `gpg --card-edit → admin → passwd → 2 (unblock)`.
2. Verify it **non-interactively**, which can't be mistyped:
   `pkcs11-tool --module <mod> --login --pin '<PIN>' --test`
   A freshly-set PIN that this accepts is provably correct; only then use ssh.

Each PW1 unblock spends the **Admin PIN (PW3)**, which has few tries. A locked
PW3 means `ykman openpgp reset` — which **destroys the very key** you're
preserving. Never guess PINs; note PW1 somewhere safe.

## Bundled setup script

`assets/yubikey-opensc-ssh-setup.sh` applies all of the above idempotently on
macOS, verifies the installed OpenSSH (>= 8.9) and OpenSC versions and the
module load, pins the Homebrew paths, and does a functional card check. It
touches only client config — never the card or any PIN.

## Side effect of `Host *`: every automated ssh becomes a card login

With `PKCS11Provider` under `Host *`, any ssh spawned by a tool — an MCP server
whose transport is ssh, an editor or agent hook, a cron job — loads the card
and, if the server accepts the card key, prompts for the PIN on whatever
controlling terminal it inherited (ssh opens `/dev/tty` directly; stdin being a
pipe does not stop it). In Claude Code this shows up as a PIN prompt painted
over the TUI at startup, only when the key is inserted. Without the card the
same ssh silently falls back to file keys or a password prompt, so the symptom
looks random. Seen 2026-10-05 (see case-log).

For automated callers, use a human-opened ControlMaster socket plus BatchMode:

    # once per session, by hand (PIN + touch happen here):
    ssh -fNM -S ~/.ssh/ctl-<name> -o ServerAliveInterval=30 -p <port> user@host
    # the tool's command:
    ssh -S ~/.ssh/ctl-<name> -o ControlMaster=no -o BatchMode=yes -p <port> user@host <cmd>

`BatchMode=yes` disables password *and* PKCS#11 PIN prompts (`pkcs11_init(!batch_mode)`),
so a missing master fails within a second instead of blocking on the terminal.
Keep such servers out of the user (global) scope so they start only in the
project that needs them.
