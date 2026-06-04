# PIN / PUK / blocked-credential recovery

The cardinal rule: **find out which applet's PIN is blocked before doing
anything.** PIV, FIDO2, and OpenPGP each have an independent PIN and an
independent retry counter. A blocked PIV PIN says nothing about FIDO2 or
OpenPGP, and the recovery path differs for each.

## Factory defaults (only if never changed)

- PIV PIN: `123456`  •  PIV PUK: `12345678`  •  PIV management key (TDES):
  `010203040506070801020304050607080102030405060708`
- OpenPGP user PIN: `123456`  •  OpenPGP admin PIN: `12345678`
- FIDO2: no factory PIN; one is set by the user on first use.

## PIV: PIN blocked → unblock with the PUK

When `ykman piv info` shows `PIN tries remaining: 0`, the PIN is blocked. Use
the PUK to set a new PIN and restore the counter:

```
ykman piv access unblock-pin                 # modern ykman (5.x); prompts for PUK + new PIN
ykman piv unblock-pin                         # older ykman syntax
```

Non-interactive form: `ykman piv access unblock-pin -p <PUK> -n <NEW_PIN>`.

**The PUK has its own counter** (default 3). If the PUK is also at 0, it's
blocked and `unblock-pin` will not work — the only path left is a full PIV
reset (see reset-recovery.md), which erases all PIV keys and certs.

### Important exception: YubiKey Bio Multi-protocol Edition (MPE)

On the Bio MPE the **PUK is shipped permanently blocked by design** — so
`ykman piv info` showing the PUK at 0 retries is *expected*, not a fault, and
`unblock-pin` cannot work. The intended PIV PIN recovery factor is the
**fingerprint (biometric)**: a successful match lets the user set a new PIN
without a PUK. If biometrics are intact, that's the recovery path. If both the
PIN is blocked and biometrics are unavailable/unenrolled, only a full PIV reset
remains.

Also note: the **YubiKey Bio FIDO Edition does not support PIV at all** — if
PIV PIN/PUK counters are visible, the device is the Multi-protocol Edition.
Confirm the exact model with `ykman info` (look at the device name).

## FIDO2: PIN blocked

FIDO2 has its own retry logic: after several wrong PINs the key forces a
re-insert, and after the counter is exhausted FIDO2 locks. **There is no PUK
for FIDO2.** The only way to clear a blocked FIDO2 PIN is to reset the FIDO2
application, which deletes all FIDO2 credentials/passkeys on the device:

```
ykman fido access change-pin                  # change PIN (if not yet blocked)
ykman fido reset                              # ERASES all FIDO2 credentials — irreversible
```

See fido2.md before resetting — resident passkeys are lost and the user must
re-register on every service.

## OpenPGP: PIN / admin PIN blocked

The OpenPGP user PIN is unblocked with the **admin PIN** (not a PUK):

```
gpg --card-edit
> admin
> passwd
# menu: 2 = unblock PIN (uses admin PIN to reset user PIN)
#       3 = change admin PIN
```

Or via ykman: `ykman openpgp access ...` for retry-counter and PIN management.
If the **admin PIN** itself is blocked, the only recovery is an OpenPGP applet
reset (`ykman openpgp reset`), which erases the on-card keys — destructive, and
catastrophic if there's no backup of the keys.

## Quick counter check across applets

```
ykman piv info        | grep -i 'tries'      # PIV PIN + PUK counters
ykman openpgp info                            # OpenPGP PIN retry counters
ykman fido info                               # FIDO2 PIN status
```

## Decision summary

- PIV PIN blocked, PUK alive → `ykman piv access unblock-pin`. Non-destructive.
- PIV PIN blocked, PUK also blocked → PIV reset only. Destroys PIV keys.
- Bio MPE, PUK shows 0 → expected; recover via fingerprint, else PIV reset.
- FIDO2 PIN blocked → FIDO2 reset only. Destroys passkeys.
- OpenPGP user PIN blocked → unblock with admin PIN. Non-destructive.
- OpenPGP admin PIN blocked → OpenPGP reset only. Destroys on-card keys.
