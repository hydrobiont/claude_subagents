# PIV, SSH, PKCS#11, and the agent layer

This is the densest and most confusing area. A YubiKey can serve SSH from two
completely different applets, through several different agents. Misdiagnosis
here is common because the symptom ("PIN accepted, but it won't authenticate")
is identical across unrelated root causes.

## First: which applet and which agent?

Two applets can hold an SSH key:

- **PIV applet** — keys in slots `9a` (PIV Authentication), `9c` (Digital
  Signature), `9d` (Key Management), `9e` (Card Authentication). Served to SSH
  via a PKCS#11 module (Yubico `libykcs11` or OpenSC `opensc-pkcs11.so`) loaded
  into OpenSSH's `ssh-agent`.
- **OpenPGP applet** — the authentication subkey (key usage `[A]`). Served to
  SSH by `gpg-agent` with `enable-ssh-support`.

**Tell them apart by the key comment in `ssh-add -l` / `ssh -v`:**

- A `cardno:XXXXXXXX` label ⇒ **gpg-agent / OpenPGP applet**.
- A label like `PIV AUTH pubkey` or a PKCS#11 path ⇒ **ssh-agent + PKCS#11 /
  PIV applet**.

Always check what the agent socket actually is:

```
echo "$SSH_AUTH_SOCK"
gpgconf --list-dirs agent-ssh-socket    # gpg-agent's ssh socket path
ssh-add -l                              # which keys, and their labels
```

If `SSH_AUTH_SOCK` equals the gpg-agent ssh socket, gpg-agent is your agent —
this matters enormously for the host-bound failure below.

## Failure mode 1: host-bound auth — "agent refused operation"

**Signature in `ssh -vvv`:**

```
get_agent_identities: ssh_agent_bind_hostkey: agent refused operation
...
Server accepts key: cardno:... RSA ...
sign_and_send_pubkey: using publickey-hostbound-v00@openssh.com ...
sign_and_send_pubkey: signing failed for RSA "cardno:..." from agent: agent refused operation
```

**What's happening.** OpenSSH 8.9+ (and by default on the client) negotiates
the *host-bound* public-key authentication extension when the server advertises
`publickey-hostbound@openssh.com` in its EXT_INFO. Host-bound signing requires
the agent to implement `session-bind@openssh.com`. **gpg-agent does not
implement it**, so it refuses the bind (`ssh_agent_bind_hostkey: agent refused
operation`) and then refuses to produce the signature — even though the key is
valid and the server already accepted it (`Server accepts key` / packet type
60 appears right before the failure).

Key tells: the failure is at *signing time*, not key offering; the key label is
`cardno:`; and there's no client option to disable host-bound auth (both the
modern client and a 8.9+ server negotiate it automatically).

> **macOS + OpenPGP-card key, "no redeploy" requirement:** the ssh-agent route
> below is often a dead end on macOS (Apple's ssh-agent rejects PKCS#11
> providers; whitelist/socket headaches). The robust fix there is **agentless**
> — load OpenSC directly with `PKCS11Provider`/`ssh -I` so ssh signs in-process
> and does host-bound itself. See `reference/openpgp-ssh-macos.md` for the
> complete, tested procedure and a setup script. The notes below still apply
> for PIV keys and non-macOS setups.

**Fix — serve the same key through OpenSSH's own ssh-agent**, which supports
`session-bind`. Test in a throwaway shell first so the user's gpg setup is
untouched:

```
unset SSH_AUTH_SOCK
eval "$(ssh-agent -s)"
gpgconf --kill scdaemon gpg-agent          # release the card so OpenSC can claim it
ssh-add -s /opt/homebrew/lib/opensc-pkcs11.so   # macOS Homebrew path; enter card PIN
ssh-add -l                                  # confirm SAME fingerprint as before
ssh user@host
```

OpenSC's OpenPGP driver exposes the same authentication subkey, so the public
key is unchanged and the server's `authorized_keys` still matches — this is a
different *agent*, not a different *key*. Because ssh-agent handles
`session-bind`, host-bound signing now succeeds.

Notes and caveats:
- OpenSC and gpg's `scdaemon` can't both hold the card simultaneously. If the
  user still needs gpg for signing/encryption, they're trading which app talks
  to the card.
- OpenSC PKCS#11 module paths vary: `/opt/homebrew/lib/opensc-pkcs11.so`,
  `/opt/homebrew/lib/pkcs11/opensc-pkcs11.so`, or
  `/usr/lib/x86_64-linux-gnu/opensc-pkcs11.so`. Find it:
  `find /opt/homebrew /usr/lib /usr/local -name 'opensc-pkcs11.so' 2>/dev/null`.
- Updating GnuPG is worth trying but historically has *not* added session-bind
  support, so don't promise it will fix it.
- To make it permanent, remove wherever `SSH_AUTH_SOCK` is pointed at gpg-agent
  (often `enable-ssh-support` in `~/.gnupg/gpg-agent.conf` plus a
  `SSH_AUTH_SOCK=$(gpgconf --list-dirs agent-ssh-socket)` line in the shell rc
  or a `launchctl setenv`), and load the PKCS#11 key into ssh-agent instead.
- Alternative: switch the server to the **PIV** key via `libykcs11` — but that
  is a *different* public key, so its pubkey must be added to the server's
  `authorized_keys` first.

## Failure mode 2: expired PIV certificate

**Signature:** `ykman piv info` shows a slot whose `Not after` date is in the
past. SSH unlocks the card (PIN accepted) but the agent offers no usable key,
or the connection silently falls back to password.

**What's happening.** Most PKCS#11 modules derive the SSH public key from the
slot's *certificate* and will not present an expired certificate's key to
ssh-agent. The keypair itself is unaffected.

**Fix — mint a fresh self-signed cert over the existing key** (keypair and
therefore SSH public key are unchanged, so no server-side edit needed):

```
ykman piv certificates export 9a cert.pem
openssl x509 -in cert.pem -pubkey -noout > pub.pem
ykman piv certificates generate -s "CN=ssh" -d 3650 9a pub.pem   # prompts for mgmt key + PIN
ykman piv info                                                    # confirm new "Not after"
```

Use the actual slot the key lives in (`9a` is the conventional SSH/auth slot;
verify with `ykman piv info`).

## Failure mode 3: touch policy

**Signature:** signing hangs or "fails" with no PIN error; the key was offered
and accepted. The YubiKey is blinking, waiting for a physical tap.

**Fix:** tell the user to touch the key when it blinks. To inspect/avoid: touch
policy is set at key generation/import time (`--touch-policy always|cached|never`
in `ykman piv keys generate/import`). It can't be changed without regenerating
the key.

## Failure mode 4: wrong slot / empty slot

`ssh-add -s` or the PKCS#11 config points at a slot with no key, or the SSH
client is configured for a slot the key isn't in. Confirm with `ykman piv info`
which slots actually contain keys, and make sure the PKCS#11 module exposes
that slot. If SSH worked before and just stopped, this is unlikely to be the
cause — look at cert expiry or agent changes instead.

## Useful PIV-SSH commands

```
ykman piv info                          # slots, keys, cert validity, PIN/PUK counters
ykman piv keys info 9a                  # detail on one slot's key
ssh-add -s /path/to/pkcs11.so           # load a PKCS#11 token into ssh-agent
ssh-add -e /path/to/pkcs11.so           # remove it
ssh-keygen -D /path/to/pkcs11.so        # print the public keys a PKCS#11 module exposes
ssh -vvv user@host                       # the authoritative diagnostic for SSH auth
```

When given an `ssh -vvv` dump, read in this order: the offered key label
(`cardno:` vs PIV), whether the server *accepts* the key (packet type 60 /
`Server accepts key`), and exactly where it fails (offering vs `sign_and_send`).
That trio almost always pins the root cause.
