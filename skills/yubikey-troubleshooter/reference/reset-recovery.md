# Reset & recovery (destructive — last resort)

Every reset here is **irreversible** and **per-applet**. A reset recovers
*access* by destroying *contents*. Always confirm with the user that losing the
keys/credentials in that applet is acceptable, and that they have backups or
alternate access to any account that depends on the device, *before* running
anything in this file.

## Before any reset, exhaust non-destructive options

- PIV PIN blocked but PUK alive → `ykman piv access unblock-pin` (no data loss).
- PIV cert expired → regenerate a self-signed cert over the existing key (no
  data loss). See piv-ssh.md.
- OpenPGP user PIN blocked → unblock with admin PIN (no data loss).
- SSH "agent refused operation" → it's an agent/protocol issue, not a broken
  device; resetting won't help. See piv-ssh.md.
- Bio MPE PUK showing 0 → expected by design; recover via fingerprint, not a
  reset. See pin-puk-recovery.md.

## Per-applet resets

```
ykman piv reset         # PIV: wipes all slots' keys + certs; PIN/PUK/mgmt key to factory
ykman fido reset        # FIDO2: wipes all passkeys/credentials (must run within ~5s of insert + touch)
ykman openpgp reset     # OpenPGP: wipes on-card keys; PINs to factory
ykman oath reset        # OATH: wipes all TOTP/HOTP secrets
```

Factory defaults after a PIV reset: PIN `123456`, PUK `12345678`, management
key `010203040506070801020304050607080102030405060708` (TDES). After OpenPGP
reset: user PIN `123456`, admin PIN `12345678`.

## "The device feels bricked"

Usually it isn't — work through these before concluding hardware failure:

1. `ykman info` — does the device enumerate at all? If yes, it's a software/
   applet issue, not dead hardware.
2. Try a different USB port, cable, and machine. Bad cables and USB-C dongles
   are a frequent cause of "dead key".
3. Check enabled interfaces: `ykman config usb --list`; re-enable an app with
   `ykman config usb -e <APP>` (e.g. `FIDO2`, `PIV`, `OPENPGP`, `OATH`).
4. Kill conflicting card consumers (`gpgconf --kill scdaemon`, close Yubico
   Authenticator / OpenSC) — contention looks like a dead card.
5. Only if the device never enumerates on any machine/port is it likely a
   genuine hardware failure (then: warranty/replacement).

## Post-reset rebuild checklist

After resetting an applet, the user has to rebuild it:

- **PIV**: set a new PIN/PUK/mgmt key, regenerate or import keys, import/mint
  certs, redistribute the public key to servers' `authorized_keys`.
- **FIDO2**: set a PIN, (Bio) re-enroll fingerprints, re-register every
  passkey/security-key on each service.
- **OpenPGP**: set PINs, restore keys from backup (or generate new and publish
  the new public key), update `git`/SSH config.
- **OATH**: re-add every TOTP account from its seed/QR or backup codes.
