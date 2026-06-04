---
name: yubikey-troubleshooter
description: >-
  Diagnose and fix YubiKey problems across all of its applications: PIV
  (smartcard auth, SSH via PKCS#11, certificates, PIN/PUK), FIDO2/WebAuthn
  (passkeys, security keys, bio), OpenPGP (gpg-agent signing/encryption/SSH
  subkeys), and OATH-TOTP. Use this skill whenever the user mentions a YubiKey,
  ykman, PIV, PKCS#11 smartcard SSH, "agent refused operation", blocked PIN or
  PUK, FIDO2 PIN, gpg-agent vs ssh-agent, an expired smartcard certificate, a
  YubiKey Bio, or wants to reset/recover a security key — even if they only
  paste an error log or `ssh -vvv` output without naming the device. Read the
  matching reference file before answering, and log notable new diagnoses to
  reference/case-log.md so the skill's domain knowledge grows over time.
---

# YubiKey Troubleshooter

A diagnostic skill for YubiKey hardware tokens. The goal is to identify *which
applet and which layer* is actually failing — because the same symptom ("it
asks for my PIN but nothing works") can come from an expired certificate, a
blocked PIN, a touch policy, or an agent that doesn't speak a required protocol
extension. Guessing wastes the user's time and can destroy keys (a reset is
irreversible). Diagnose first, act second.

## How to use this skill

1. **Identify the applet.** A YubiKey is really five independent
   applications living on one device: PIV, FIDO2/U2F, OpenPGP, OATH, and
   YubiHSM-auth. They have *separate* PINs, separate retry counters, and
   separate reset commands. The first job in any case is to figure out which
   one the user is actually touching. See "Triage" below.
2. **Read the matching reference file** in `reference/` before giving
   commands. Each file has the real failure modes, the diagnostic commands, and
   the fixes for one area. Don't answer PIV-SSH questions from memory when
   `reference/piv-ssh.md` has the exact gotchas.
3. **Gather state before changing anything.** `ykman info` and the
   applet-specific `info` command are cheap and prevent destructive mistakes.
4. **Prefer non-destructive fixes.** Regenerating a certificate, switching
   agents, or unblocking a PIN with a PUK all preserve key material. A full
   applet reset erases keys and certs permanently and should be the last
   resort, clearly flagged as irreversible.
5. **Log the case.** If you diagnose something not already covered, append a
   short entry to `reference/case-log.md` so the next run benefits. This is how
   the skill accumulates domain knowledge.

## Triage: which applet is failing?

Start here. Run `ykman info` to see firmware version and which applications are
enabled, then narrow by symptom:

- **SSH, smartcard login, `ssh-add -s`, PKCS#11, "agent refused operation",
  `cardno:` keys, certificate expiry** → PIV *or* OpenPGP, depending on which
  agent holds the key. This is the most common and most confusing area.
  Read `reference/piv-ssh.md`. The `cardno:` label specifically means
  gpg-agent (OpenPGP applet), not PIV.
- **"SSH broke after an OpenSSH/macOS upgrade", `agent refused operation` with
  a `cardno:` key, "host-bound", want to keep using the OpenPGP key with no
  redeploy** → this is the gpg-agent-can't-do-host-bound problem; the fix is to
  serve the OpenPGP key agentlessly via OpenSC `PKCS11Provider`/`ssh -I`. Read
  `reference/openpgp-ssh-macos.md` (full macOS playbook + bundled setup script
  `assets/yubikey-opensc-ssh-setup.sh`).
- **"PIN tries remaining: 0", blocked PIN, need to use the PUK, forgot PIN** →
  Read `reference/pin-puk-recovery.md`. Note PIV and FIDO2 and OpenPGP each
  have their *own* PIN and counter.
- **Passkeys, WebAuthn, "security key", FIDO2 PIN, browser won't recognize the
  key, fingerprint enrollment, YubiKey Bio** → Read `reference/fido2.md`.
- **GPG signing/encryption, `gpg --card-status`, "No secret key", commit
  signing, gpg-agent prompts** → Read `reference/openpgp.md`.
- **TOTP / 2FA codes, Yubico Authenticator, OATH password** →
  Read `reference/oath.md`.
- **Anything that ends in "I just want it working again from scratch", reset,
  factory defaults, device feels bricked** → Read
  `reference/reset-recovery.md`. Confirm with the user that key loss is
  acceptable before any reset.

For a fast command lookup across all areas, see `reference/cheatsheet.md`.

## Core principles to carry into every case

**Separate PINs.** The single most common confusion: the PIV PIN, the FIDO2
PIN, and the OpenPGP PIN are different secrets with different retry counters.
"My PIN is blocked" is meaningless until you know *which* applet. A healthy
`ykman piv info` (3/3 tries) does not mean FIDO2 or OpenPGP is healthy.

**The agent matters as much as the key.** For SSH especially, the key can be
perfectly valid and authorized on the server while the *agent* in front of it
(gpg-agent, ssh-agent, a PKCS#11 module) is what fails. Modern OpenSSH (9.x+)
negotiates the host-bound public-key extension (`publickey-hostbound`), which
requires the agent to support `session-bind@openssh.com`. gpg-agent has
historically lacked this, producing `agent refused operation` even though the
card and key are fine. Always check which agent `SSH_AUTH_SOCK` points at.

**Certificates expire; keys don't.** A PIV slot's certificate can expire while
the underlying keypair stays valid. Many PKCS#11 modules refuse to present an
expired certificate's key to ssh-agent, breaking SSH. The fix is usually to
mint a fresh self-signed cert over the *existing* key — no server-side change
needed because the public key is unchanged.

**Touch and biometric policies fail silently.** If a slot requires touch, the
key blinks and the operation times out / "fails" if the user doesn't tap it.
This looks like an auth failure but isn't. Watch for the blink.

**Reset is irreversible.** `ykman <app> reset` wipes that applet's keys, certs,
and PINs back to factory defaults. It recovers *access* by destroying
*contents*. Never suggest it casually, and never as a first move when keys
might still be recoverable.

## Output style

Lead with the diagnosis — name the failing applet and layer — then give the
minimal non-destructive fix, then escalate only if needed. Show the exact
commands. When a step is destructive, say so plainly before the command. Keep
explanations tied to evidence from the user's own output (counters, log lines,
slot data) rather than generic advice.
