# OpenPGP applet (gpg-agent, signing, encryption, SSH auth subkey)

The OpenPGP applet holds up to three subkeys — Signature `[S]`, Encryption
`[E]`, Authentication `[A]` — accessed through GnuPG's `gpg-agent` /
`scdaemon`. It is independent of PIV. Its user PIN and admin PIN are separate
from every other applet's secrets.

## Orientation commands

```
gpg --card-status                  # serial, key fingerprints, PIN retry counters, name/URL
ykman openpgp info                 # ykman's view of the OpenPGP applet
gpgconf --list-dirs                # socket paths (agent, agent-ssh, scdaemon)
gpg --list-keys / --list-secret-keys
```

In `gpg --card-status`, secret keys present on the card show as `ssb>` (the `>`
means "stub: lives on a smartcard").

## Common cases

**"No secret key" / gpg can't find the on-card key.** The local keyring lacks
the stub pointing at the card. Re-import it:

```
gpg --card-edit
> fetch                # if a key URL is set on the card
# or
gpg --card-status      # often re-creates the stubs
```

If keys were used on another machine, import the public key and let
`--card-status` generate the secret-key stubs.

**Signing/decryption hangs or fails.**
- Touch policy: many setups require a tap for sign/auth/decrypt. The key
  blinks; the operation fails if not touched. Check/set:
  `ykman openpgp keys set-touch sig on` (and `aut`, `enc`).
- Stale agent: `gpgconf --kill gpg-agent scdaemon` then retry; a wedged
  scdaemon is a frequent culprit, especially after sleep/USB re-enumeration.
- Another app holding the card (OpenSC PKCS#11, Yubico Authenticator) blocks
  scdaemon. Close it or kill scdaemon.

**PIN / admin PIN blocked.** See pin-puk-recovery.md — user PIN is unblocked
with the admin PIN; a blocked admin PIN means only an applet reset remains.

**Git commit signing fails.** Verify `git config user.signingkey` matches a key
on the card, `gpg.program` points at the right gpg, and `gpg --card-status`
shows the signature subkey. `echo test | gpg --clearsign` isolates whether the
problem is git or gpg/card.

## OpenPGP for SSH (the `cardno:` keys)

If `gpg-agent` runs with `enable-ssh-support`, the OpenPGP authentication
subkey `[A]` is offered to SSH. In `ssh-add -l` it appears as
`cardno:XXXXXXXX`. This is the source of most "is it PIV or OpenPGP?"
confusion — see piv-ssh.md, especially the host-bound / `session-bind`
limitation that makes gpg-agent fail with modern OpenSSH.

```
gpgconf --list-dirs agent-ssh-socket     # the socket SSH_AUTH_SOCK should point to for gpg-ssh
grep enable-ssh-support ~/.gnupg/gpg-agent.conf
```

## scdaemon vs other card consumers

Only one process can hold the smartcard's CCID interface at a time. `scdaemon`
(gpg), OpenSC's PKCS#11, and Yubico Authenticator will fight over it. Symptoms:
intermittent "card not present", ` scdaemon` errors, or one tool working only
after another is closed. Resolution: pick one consumer per workflow, or kill
the other (`gpgconf --kill scdaemon`) when switching. `disable-ccid` in
`scdaemon.conf` can force gpg to use PC/SC and coexist on some systems.

## Reset (destructive)

```
ykman openpgp reset            # wipes on-card OpenPGP keys + resets PINs to factory
```

Only safe if the keys are backed up off-card (or were generated off-card and
can be re-imported). On-card-generated keys with no backup are gone forever.
