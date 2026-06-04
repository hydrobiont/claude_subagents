# FIDO2 / WebAuthn / U2F

The FIDO2 application handles passkeys (resident/discoverable credentials),
WebAuthn second-factor, and legacy U2F. It is fully independent of PIV and
OpenPGP — its own PIN, its own reset.

## Key facts

- **No PUK.** FIDO2 has only a PIN with a retry counter. There is no
  unblock-with-a-recovery-code path. A blocked FIDO2 PIN can only be cleared by
  resetting the FIDO2 app, which erases all credentials.
- **PIN retry behavior.** Wrong PIN attempts decrement a counter; after a few
  the key requires re-insertion, and at 0 FIDO2 locks until reset. The exact
  count is firmware-defined (typically 8 total, with re-insert prompts along
  the way).
- **Reset must be prompt after insertion.** `ykman fido reset` only works
  within a short window (≈5s) of plugging the key in, and requires a touch.
  This is an anti-tamper measure.

## Common cases

**Browser/site won't recognize the key.**
- Confirm FIDO2 is enabled and the firmware supports it: `ykman info`,
  `ykman fido info`.
- USB transport / interface: `ykman config usb --list` and ensure FIDO2 is on.
  `ykman config usb -e FIDO2` to enable.
- Try a different USB port/cable; some hubs and USB-C adapters break HID.
- NFC: not all keys have it; tap placement matters.

**Forgot / blocked FIDO2 PIN.** No recovery without reset:

```
ykman fido access change-pin           # change while still known/unblocked
ykman fido reset                        # ERASES all passkeys/credentials — irreversible
```

After a reset, every service where the key was registered as a passkey or
security key must be re-enrolled. Make sure the user has another factor or
recovery method for those accounts *before* resetting, or they can lock
themselves out.

**Too many resident keys / "no space".** Discoverable credentials consume slots
(commonly 25). List and prune:

```
ykman fido credentials list
ykman fido credentials delete <id>
```

## YubiKey Bio (fingerprint)

- **Bio FIDO Edition**: FIDO2/U2F only — no PIV, no OpenPGP, no OATH.
- **Bio Multi-protocol Edition (MPE)**: FIDO2 + PIV with biometrics.
- Fingerprint enrollment and management:

```
ykman fido fingerprints list
ykman fido fingerprints add "right-index"
ykman fido fingerprints delete <id>
```

- A FIDO2 PIN must be set before fingerprints can be enrolled — the PIN is the
  fallback/recovery factor for biometrics.
- If fingerprints stop matching, the PIN still works; if both are exhausted,
  FIDO2 reset is the only path.

## Diagnostic commands

```
ykman info                     # which apps + transports are enabled
ykman fido info                # FIDO2 PIN status, options
ykman fido credentials list    # resident credentials
ykman fido fingerprints list   # enrolled fingerprints (Bio)
```
