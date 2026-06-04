# Case log — accumulated diagnoses

This is the skill's growing memory. When a YubiKey case is diagnosed that isn't
already well covered by the reference files, append a concise entry here so
future runs benefit. Keep entries short and evidence-led.

**How to add an entry (instructions for the skill):**
- Append, don't rewrite. Newest at the top of the "Cases" section.
- Use the template below. Capture the *distinguishing signal* (the exact log
  line, counter, or command output that pinned the diagnosis) — that's what
  makes future triage fast.
- If a case reveals a fix that generalizes, also fold it into the relevant
  `reference/*.md` file, not only here.
- Strip secrets: never record real PINs, PUKs, private keys, or full serials.

**Template:**
```
### <short title> — <date>
- Applet/layer: <PIV | FIDO2 | OpenPGP | OATH | agent>
- Symptom: <what the user saw>
- Distinguishing signal: <the exact line/counter/output that identified it>
- Root cause: <one sentence>
- Fix: <non-destructive fix; note if destructive>
- Notes: <gotchas, environment specifics>
```

---

## Cases

### Deployed OpenPGP RSA key over modern (host-bound) SSH, no redeploy — 2026-06-04
- Applet/layer: OpenPGP authentication subkey (RSA), client agent/PKCS#11.
- Goal: keep using the RSA key already in every server's authorized_keys; OpenSSH 10.x client now forces host-bound, which gpg-agent can't satisfy.
- Why the obvious paths failed: (1) gpg-agent — no `session-bind`, can't host-bind. (2) ssh-agent + OpenSC — macOS Apple ssh-agent refuses external PKCS#11 providers; even Homebrew ssh-agent was defeated by a persistent agent relocating `SSH_AUTH_SOCK` into `~/.ssh/agent/` and by the `-P` whitelist matching the *resolved* Homebrew Cellar realpath. (3) OpenSC defaulted to the PIV applet (ECCP384, slot 9D) — wrong key, not in authorized_keys.
- Winning solution: **`ssh -I <opensc-pkcs11.so>` — load the PKCS#11 module directly in the ssh process, NO agent.** ssh does host-bound itself in-process (`bound agent to hostkey`), so the gpg-agent/ssh-agent problems vanish. Force OpenSC to the OpenPGP applet with `card_drivers = openpgp, internal;` (in a file pointed to by `OPENSC_CONF`) so it exposes the RSA auth key (matched the deployed `oYDPI…` fingerprint) instead of the PIV key. Server accepted it, no redeploy.
- Card contention: gpg's scdaemon grabs the YubiKey CCID exclusively and collides with OpenSC. Add `disable-ccid` to `~/.gnupg/scdaemon.conf` (scdaemon then shares via PC/SC) and `gpgconf --kill all` right before connecting.
- PIN trap (important): repeated `ssh -I` attempts with a *wrong* PIN silently decremented and then LOCKED PW1; the failures showed as `PKCS#11 login failed: error 48` (CKR_DEVICE_ERROR) then `PIN locked` (CKR_PIN_LOCKED 0xa4) — easy to misread as contention. Before burning attempts via interactive ssh, set a known PIN and verify it non-interactively with `pkcs11-tool --module <mod> --login --pin <PIN> --test`. A freshly-set PIN that the test accepts proves it's correct; only then use ssh. Never repeatedly guess — PW1 unblock spends the Admin PIN (PW3), and a locked PW3 forces `ykman openpgp reset`, which destroys the very key you're trying to preserve.
- macOS specifics: client must be Homebrew's ssh (`/opt/homebrew/bin/ssh`, loads the module in-process fine); Apple's `/usr/bin/ssh-agent` rejects third-party PKCS#11 providers.



### gpg-agent refuses host-bound SSH signature — 2026-06-04
- Applet/layer: OpenPGP authentication subkey, served via gpg-agent (agent layer).
- Symptom: SSH to a server fell back to password; card accepted PIN but auth failed. `cardno:` RSA key.
- Distinguishing signal: `ssh -vvv` showed `ssh_agent_bind_hostkey: agent refused operation`, then `Server accepts key`, then `sign_and_send_pubkey: using publickey-hostbound-v00@openssh.com` followed by `signing failed ... agent refused operation`. Client OpenSSH 10.2, server OpenSSH 9.2; key labeled `cardno:`.
- Root cause: OpenSSH negotiated host-bound public-key auth, which needs the agent to support `session-bind@openssh.com`; gpg-agent doesn't implement it, so it refuses the signature even though the key is valid and accepted.
- Fix (non-destructive): serve the same OpenPGP auth subkey through OpenSSH's own ssh-agent via OpenSC PKCS#11 (`unset SSH_AUTH_SOCK; eval "$(ssh-agent -s)"; gpgconf --kill scdaemon gpg-agent; ssh-add -s /opt/homebrew/lib/opensc-pkcs11.so`). Same public key, so server `authorized_keys` unchanged. ssh-agent supports session-bind, so host-bound signing succeeds.
- Notes: There is no client option to disable host-bound auth. Updating GnuPG has historically NOT added session-bind support. OpenSC and gpg's scdaemon contend for the card — pick one consumer.
- On GnuPG 2.5.20 the `ssh_agent_bind_hostkey: agent refused operation` line still appears, i.e. gpg-agent does not advertise `session-bind@openssh.com`. That refusal is genuine and PIN-independent. However — do NOT over-conclude from it that the *whole* auth failure is session-bind: a blocked card PIN produces an identical-looking `agent refused operation` at the signing step.
- Disambiguation tip (and a lesson learned the hard way): a blocked card PIN can ALSO produce `agent refused operation`. To tell them apart you must FIRST actually restore the PIN and VERIFY the counter changed (`gpg --card-status` PW1 goes 0→3), *then* retry. Don't trust a verbal "we unblocked it" — confirm with `card-status`. In one case the unblock silently never ran (PW3 still at 3 proved no admin auth was consumed), so the "PIN fixed, failure unchanged → must be session-bind" reasoning was invalid because the control was never met. The session-bind refusal shows at `get_agent_identities` (before signing); a PIN/touch failure shows only at `sign_and_send_pubkey` after the key is accepted — but isolate them empirically, one variable at a time, rather than reasoning from the log alone.
- RESOLVED / confirmed: once PW1 was genuinely restored (`PIN retry counter : 3 0 3`) the SSH failure was byte-for-byte identical — same `ssh_agent_bind_hostkey` refusal, same `sign_and_send_pubkey ... agent refused operation`, **with no pinentry prompt and no touch blink**. That "fails before the card is ever touched" signature is the clincher: a blocked PIN or missing touch fails AFTER the card op begins, so their absence proves the refusal is purely the host-bound/session-bind gap. Net: gpg-agent 2.5.20 cannot serve a modern (8.9+) host-bound SSH handshake; fix is ssh-agent + PKCS#11 (OpenSC for the same OpenPGP key, or libykcs11 for a PIV key). The blocked PIN was a genuine but independent fault, worth fixing on its own.

### OpenPGP user PIN blocked on a YubiKey 5 — counter reads `0 0 3` — 2026-06-04
- Applet/layer: OpenPGP (PW1 user PIN). Device: "Yubico YubiKey OTP FIDO CCID" (a 5-series, NOT a Bio).
- Symptom: user thought a PUK was needed; SSH via the `cardno:` key failed.
- Distinguishing signal: `gpg --card-status` → `PIN retry counter : 0 0 3`. The three fields are **PW1 (user) / reset-code / PW3 (admin)**, so `0 0 3` = user PIN blocked, reset code unusable, admin PIN has 3 tries.
- Root cause: blocked OpenPGP user PIN. (Note: OpenPGP has no PUK — the earlier "use a PUK" framing doesn't apply here.)
- Fix (non-destructive): `gpg --card-edit` → `admin` → `passwd` → option `2` (unblock PIN), enter admin PIN, set new user PIN. Default admin PIN `12345678` if never changed.
- Notes: PW3 only had 3 tries and reset code was 0, so a wrong admin PIN risks blocking PW3 → then only `ykman openpgp reset` (destroys on-card keys) remains. Confirm the admin PIN before trying. Also seen on this card: `UIF setting: Auth=on` → SSH auth requires a physical touch (key blinks).

### PIV slot certificate expired, SSH stopped working — 2026-06-04
- Applet/layer: PIV (certificate, not key).
- Symptom: SSH that previously worked stopped; PIN accepted but no usable key offered.
- Distinguishing signal: `ykman piv info` slot showed `Not after` date in the past (cert expired ~1 year prior) while the keypair was intact.
- Root cause: PKCS#11 modules won't present an expired certificate's key to ssh-agent.
- Fix (non-destructive): mint a fresh self-signed cert over the existing key — `ykman piv certificates export <slot> cert.pem; openssl x509 -in cert.pem -pubkey -noout > pub.pem; ykman piv certificates generate -s "CN=ssh" -d 3650 <slot> pub.pem`. Public key unchanged, no server-side edit.
- Notes: In this conversation the expired 9D cert turned out to be a red herring for the SSH failure (the real key was the OpenPGP `cardno:` key) — but the expiry pattern is a genuine, common cause worth checking first.

### YubiKey Bio MPE shows PUK with zero retries by default — 2026-06-04
- Applet/layer: PIV on YubiKey Bio Multi-protocol Edition.
- Symptom: user worried the PUK was blocked because `ykman piv info` showed 0 PUK retries.
- Distinguishing signal: device is a Bio MPE; PUK at 0 from factory with no prior use.
- Root cause: by design — the Bio MPE ships the PUK permanently blocked because the fingerprint is the intended PIN-recovery factor.
- Fix: not a fault; recover a blocked PIV PIN via biometric match. If PIN blocked AND biometrics unavailable, only `ykman piv reset` (destructive) remains.
- Notes: Bio FIDO Edition has no PIV at all. Confirm model with `ykman info`.
