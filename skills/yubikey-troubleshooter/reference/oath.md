# OATH (TOTP / HOTP 2FA codes)

The OATH applet stores TOTP/HOTP secrets and generates 2FA codes, used via the
Yubico Authenticator app or `ykman oath`. Independent of PIV/FIDO2/OpenPGP.

## Orientation

```
ykman oath info                       # whether a password is set, etc.
ykman oath accounts list              # stored credentials (issuer:account)
ykman oath accounts code <query>      # generate a code
```

## Common cases

**Codes rejected by the service.**
- Almost always **clock skew**. TOTP depends on time; if the host clock is off
  by more than the step window (usually 30s), codes fail. Sync the clock
  (`sntp`/NTP). The YubiKey itself has no clock — the *host* provides time, so
  the computer/phone generating the code must be accurate.
- Wrong account or duplicate entries for the same issuer — confirm with
  `accounts list`.

**Forgot the OATH password.** The OATH applet can be protected by a password
(distinct from any PIN). If forgotten, there is no recovery; the OATH app must
be reset, which **erases all stored TOTP secrets**:

```
ykman oath access change            # change/set/remove password (if known)
ykman oath reset                    # ERASES all OATH accounts — irreversible
```

Before resetting, make sure the user has the original TOTP seeds or backup
codes for each service, or they'll be locked out of those 2FA accounts.

**Adding / removing accounts.**

```
ykman oath accounts add <name> <base32-secret> [--touch]
ykman oath accounts uri <otpauth://...>      # add from an otpauth URI/QR
ykman oath accounts delete <query>
```

**Touch-required codes.** If an account was added with `--touch`, the key must
be tapped to emit the code; otherwise it appears to do nothing.

## Capacity

The OATH applet holds a finite number of credentials (commonly 32). If adds
fail, prune unused accounts with `accounts delete`.
