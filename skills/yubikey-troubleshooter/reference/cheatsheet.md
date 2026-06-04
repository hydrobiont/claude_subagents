# YubiKey command cheatsheet

Fast lookup across all applets. `ykman` = YubiKey Manager CLI. Install:
`brew install ykman` (macOS), `apt install yubikey-manager` (Debian/Ubuntu),
`pip install yubikey-manager`.

## Device-wide

```
ykman info                         # firmware, serial, which apps + transports enabled
ykman list                         # connected devices + serials
ykman config usb --list            # USB interfaces
ykman config usb -e FIDO2          # enable an app over USB (PIV/OPENPGP/OATH/FIDO2/OTP)
ykman config usb -d OTP            # disable an app
```

## PIV

```
ykman piv info                     # slots, key/cert info, PIN+PUK counters, cert validity
ykman piv keys info 9a             # one slot
ykman piv access change-pin
ykman piv access change-puk
ykman piv access unblock-pin       # PIN blocked → use PUK (5.x). Older: ykman piv unblock-pin
ykman piv access change-management-key
ykman piv certificates export 9a out.pem
ykman piv certificates generate -s "CN=ssh" -d 3650 9a pub.pem   # self-signed over existing key
ykman piv keys generate --touch-policy always 9a pub.pem
ykman piv reset                    # DESTRUCTIVE
```

## FIDO2

```
ykman fido info
ykman fido access change-pin
ykman fido credentials list
ykman fido credentials delete <id>
ykman fido fingerprints list                 # Bio
ykman fido fingerprints add "label"          # Bio
ykman fido reset                              # DESTRUCTIVE — within ~5s of insert + touch
```

## OpenPGP

```
gpg --card-status                  # card overview, PIN counters, key fingerprints
gpg --card-edit                    # admin > passwd  (unblock/change PINs), fetch, etc.
ykman openpgp info
ykman openpgp keys set-touch sig on            # require touch for signing (also aut/enc)
ykman openpgp reset                # DESTRUCTIVE
gpgconf --list-dirs                # socket paths
gpgconf --list-dirs agent-ssh-socket
gpgconf --kill scdaemon gpg-agent  # restart wedged daemons / release card
```

## OATH

```
ykman oath info
ykman oath accounts list
ykman oath accounts code <query>
ykman oath accounts add <name> <base32-secret> [--touch]
ykman oath accounts uri "otpauth://..."
ykman oath accounts delete <query>
ykman oath access change           # set/change/remove OATH password
ykman oath reset                   # DESTRUCTIVE
```

## SSH / agents

```
echo "$SSH_AUTH_SOCK"
ssh-add -l                         # listed keys + labels (cardno: => gpg-agent/OpenPGP)
ssh-add -s /opt/homebrew/lib/opensc-pkcs11.so    # load PKCS#11 token into ssh-agent
ssh-add -e /opt/homebrew/lib/opensc-pkcs11.so    # remove it
ssh-keygen -D /opt/homebrew/lib/opensc-pkcs11.so # print pubkeys a PKCS#11 module exposes
ssh -vvv user@host                 # authoritative SSH auth diagnostic
gpgconf --list-dirs agent-ssh-socket
```

PKCS#11 module locations (varies):
```
find /opt/homebrew /usr/lib /usr/local /usr/lib64 -name 'opensc-pkcs11.so' 2>/dev/null
find /opt/homebrew /usr/lib /usr/local -name 'libykcs11*' 2>/dev/null
```

## Factory defaults

| Applet  | Default secret(s) |
|---------|-------------------|
| PIV     | PIN `123456`, PUK `12345678`, mgmt key `0102…0708` (TDES, 24 bytes) |
| OpenPGP | user PIN `123456`, admin PIN `12345678` |
| FIDO2   | no factory PIN (user sets on first use) |
