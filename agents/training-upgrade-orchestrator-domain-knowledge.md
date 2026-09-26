# Training Upgrade Orchestrator — Domain knowledge

Persistent notes accumulated by the `training-upgrade-orchestrator` agent across invocations. The agent reads this file at the start of every run and appends durable lessons when it finishes — VM-recipe corrections, battery-procedure fixes, delegation-contract changes, per-track quirks. Newest entries on top. Keep entries dated; edit superseded facts rather than stacking contradictions.

<!-- entries below; newest on top -->

## 2026-07-16 — DBA1 dba-01 executed (17→18, theory-only, no VM)

- **dba-01 = 64 reveal slides, theory.md ~1490 lines, no demo.md.** `gmake -s dba-01` builds in ~3 s. Media are NOT in the chapter dir — they resolve from the shared `handbooks/medias/` (build root); a chapter-relative existence check falsely reports "MISSING". Confirm media against `handbooks/medias/`, not `chapters/<id>/medias/`.
- **Proposal line numbers drift from the live file — match on content.** This run: dba-01-02's track-header `version:` was line 4, not the proposal's cited `:5`; dba-01-06's EOL-notes paragraph had a middle sentence ("This means there will be no more minor updates…") the proposal quote omitted, so my first Edit old_string didn't match. Always grep the live text before the Edit.
- **Static-check shell gotcha:** literal ```` ``` ```` inside a double-quoted `echo`/`printf` triggers zsh command substitution (`unmatched "` error). Use a `FENCE=$(printf '```')` variable or single-quote the string. dba-01 fence tally: 12 lines = 6 ```` ```sql ```` openers + 6 bare closers (all pre-existing SQL-in-notes).
- **global.md date ↔ header version convention:** `date: August 2026` pairs with `version: "2026.08"`. The builder date-consistency check passes on that pairing. global.md is the shared cross-track file — only touched here under an explicit user scoped-exception (decision 1); flag that it re-dates every track's build.
- **Overflow sweep:** at viewport = config = 1440×900, `.reveal .slides` box measures exactly 1440×900 (Reveal scale 1), so `section.scrollHeight > 900` is a true test. New "Version 18" slide (8 bullets) rendered 517 px → 383 px headroom; all 64 slides 0 overflow. Console always shows 1 error + 1 warning = favicon.ico 404 + `apple-mobile-web-app-capable` meta deprecation — both environmental (http.server / converter shell), never chapter content.
- **Background HTTP server:** `python3 -m http.server 8765 --bind 127.0.0.1 --directory <buildpath> &` inside a `run_in_background` Bash call detaches as an orphan and keeps serving after the launcher shell reports "completed"; `curl` to confirm up; `pkill -f "http.server 8765"` to stop (verify with a post-kill curl → 000).
- **Fact-checker (training-fact-checker) confirmed all 14 changed v18 claims.** Reusable facts it nailed down: PG18 GA 2025-09-25; 14 May 2026 minors = 18.4/17.10/16.14/15.18/14.23; **v13's final minor was 13.23 — verified via the release index, NOT by offset arithmetic**; EOLs v12 2024-11-21 / v13 2025-11-13 / v14 2026-11-12 / v18 2030-11-14; next minor 2026-08-13; `io_method` default `worker` (aio.h:42); v19 Beta 2 shipped 2026-07-16 (so "next major = 19" holds). Its agentId for follow-ups this session: af3b807997eb1cbdb.
- **Wording/style edits land AFTER the first build+sweep, so rebuild+re-sweep on the final text** before reporting a clean build/overflow — otherwise the report describes a stale artifact.

## 2026-07-15 — Seed: throwaway demo VM recipe (GCP)

User policy (decided 2026-07-15): DBA demo rehearsals run on a **fresh disposable VM per run**, cloned from dn-test-03's shape, provisioned via gcloud CLI, and **deleted — not stopped — when the tests end**. Clean machine = faithful trainee experience.

- Project `dba-test-430310`, zone `europe-west1-c`, account `ik@dataegret.com`.
  Auth check first: `gcloud auth print-access-token >/dev/null` — if it demands reauth, the USER must run `! gcloud auth login` (interactive; the agent cannot). Tokens in this org expire periodically.
- Shape (= dn-test-03): `e2-standard-4` (4 vCPU/16 GB), 40 GB boot disk, Ubuntu 24.04 LTS, default VPC **with external IP** (PGDG apt needs outbound internet; the dn-test siblings run this way). ~$0.13/h — a full rehearsal costs well under $1.
- Naming/labels — the deletion-safety contract: name `tr-demo-<track>-<mmdd>`, labels `purpose=training-demo,managed-by=claude`. Only instances matching BOTH may ever be created or deleted. `dn-test-*` and `stg-*` are other people's machines.

```bash
# 0. leftover sweep (report strays before creating anything)
gcloud compute instances list --project=dba-test-430310 --filter="name~^tr-demo-"

# 1. per-run ssh key (disposable, lives in the session scratchpad)
ssh-keygen -t ed25519 -N '' -f "$SCRATCH/tr-demo-key" -C ik

# 2. create
gcloud compute instances create tr-demo-dba1-0715 \
  --project=dba-test-430310 --zone=europe-west1-c \
  --machine-type=e2-standard-4 \
  --image-family=ubuntu-2404-lts-amd64 --image-project=ubuntu-os-cloud \
  --boot-disk-size=40GB \
  --labels=purpose=training-demo,managed-by=claude \
  --metadata=ssh-keys="ik:$(cat "$SCRATCH/tr-demo-key.pub")"
# (if the image family name errs: gcloud compute images list --project=ubuntu-os-cloud --filter="family~2404")

# 3. connect — IdentitiesOnly=yes is ESSENTIAL: without it ssh offers the user's
#    YubiKey PIV key first and dies with "agent refused operation"
gcloud compute ssh tr-demo-dba1-0715 --project=dba-test-430310 --zone=europe-west1-c \
  --ssh-key-file="$SCRATCH/tr-demo-key" --command='...' -- -o IdentitiesOnly=yes
# guest agent needs ~30–60 s after RUNNING to install the metadata key — retry, don't panic.
# OS Login is OFF in this project (metadata keys are the mechanism). Metadata-key users get
# passwordless sudo on GCE (google_sudoers) — apt/pg_ctlcluster demos work as written.
# If direct SSH is firewalled, add --tunnel-through-iap to the same command.

# 4. delete (ALWAYS — also on failed rehearsals) + verify
gcloud compute instances delete tr-demo-dba1-0715 --project=dba-test-430310 \
  --zone=europe-west1-c --quiet
gcloud compute instances describe tr-demo-dba1-0715 --project=dba-test-430310 \
  --zone=europe-west1-c 2>&1 | grep -q "was not found" && echo "deletion verified"
```

Rehearsal discipline: run `demo.md` top-to-bottom in order (state carries between steps); batch commands per SSH call where possible (each call has setup overhead); capture stdout/stderr verbatim per step; `DEBIAN_FRONTEND=noninteractive` for apt; demos are expected to end with their own cleanup steps (user policy: demos self-clean) — verify the cleanup section exists and runs, and note its absence as a finding. The VM is deleted regardless.

## 2026-07-15 — Seed: build + overflow battery

- Build root `~/work/de/trainings2025/training/handbooks/`; **gmake, not make** (macOS system make 3.81 chokes on `define VAR =`). `gmake -s <chapter>` / `gmake -s <track>`. Preflight: Docker daemon up; images `pandoc/minimal`, `pandoc/extra`, `astefanutti/decktape`; converter `~/.dataegret/markdown-converter/converter.sh`. Outputs `_build/<chapters|training-tracks>/<id>/<id>.{handout,slides.reveal}.html`; the intermediate `_build/.../<id>.slides.md` shows exactly what pandoc got — first stop when diagnosing.
- Static checks before building (builder discipline): exactly one `# H1`; `---` separators with blank lines around; `<div class="notes">`/`</div>` counts equal; every `medias/<file>` exists; code fences balanced + language-tagged; no tab characters inside notes divs; `common/global.md` `date:` agrees with the chapter/track `header.md` `version:` (**global.md is shared across ALL tracks — read-only for this agent; a needed date change is reported to the user, never applied**); demo files whose preamble contains trainer-only login material (gcloud ssh, sudo -u postgres, instance names) must carry the `<!-- the part above is to be removed later for handouts -->` marker or it leaks into handouts.
- Overflow sweep (slides render into a fixed 1440×900 reveal frame; excess is silently clipped — static checks cannot see it):
  1. `cd _build/chapters/<id> && python3 -m http.server 8765` (background; browsers block file://).
  2. Playwright → `http://localhost:8765/<id>.slides.reveal.html`.
  3. Evaluate: iterate `Reveal.slide(i)` over all `.reveal .slides > section`, flag `scrollHeight > 900 || scrollWidth > 1440`, report index + heading + overshoot px (full snippet in project memory `slide_overflow_check`).
  4. For each hit, measure child heights to find the culprit.
  - Fix patterns: split the slide; table >~6 multi-line rows → split; heading wrapped to two lines → shorten; image too tall → `height` ≤ 400px; trailing list after a wide table → own slide. Re-build and re-sweep after fixes.

## 2026-07-15 — Seed: wording, style, fact-check contracts

- **Wording** = the `tighten-prose` skill discipline on every touched slide/notes block: cut filler words, keep identifiers, version qualifiers, negations, numbers; concrete facts over vague phrasing. Plus define-before-use: any term the upgrade introduces must be defined earlier in the same chapter (project memory `define_before_use`).
- **Style** = `canonical-tech-names` skill over touched prose — PostgreSQL, pgBadger, pgBackRest, pgbench, systemd, Ubuntu spelled as the projects spell themselves; NEVER edit identifiers inside code blocks/commands/captured output (flag, don't fix). Plus slide voice (project memory `slide_voice`): plain declarative reference tone like the DBA chapters; no meta-narrative ("this is the toolbelt for…"), no flourish openers, no curriculum talk in notes divs. British English throughout (optimise, behaviour).
- **Fact-check** = spawn `training-fact-checker` scoped to the chapter's changed slide ranges + notes, target version = TO. Expect per-claim verdicts (CONFIRMED / CONTRADICTED / OUTDATED / IMPRECISE / UNVERIFIABLE) with citations. CONTRADICTED/OUTDATED on introduced text → fix and re-run, or mark the proposal item `blocked` in the report. The checker is independent on purpose — don't pre-negotiate its verdicts.
- **Demo SQL routing**: `training-sql-tester` is wired to the shared `stg-devpg-01-gcp-instance01` (library DB, tunnel on localhost:5433, YubiKey or test-access window — see that agent's spec). Route ONLY DEVPG/SQL-level verification there. DBA OS-level demos (apt, pg_ctlcluster, cluster create/drop) NEVER run on it — throwaway VM only.

## 2026-07-15 — Seed: git + scope rails (standing user rules)

- The user commits and pushes **themselves** — staging (`git add` of files this agent changed) is the ceiling; no commit, no push, no PR creation. No `Co-Authored-By: Claude` anywhere, ever.
- The user edits files in parallel with agent runs: immediately before staging, re-diff every target file and reconcile — never clobber, never sweep unrelated hunks into the stage.
- Write scope per run = the named track's chapters + `training-tracks/<track>/` on the named branch (current run: `dba1_pg18_update`). Verify the branch with `git -C ~/work/de/trainings2025/training branch --show-current` before the first edit.

## 2026-07-15 — Seed: DBA1 17→18 run specifics

- Chapters: dba-01 (theory only — no demo rehearsal), dba-02 (PGDG apt install walkthrough on Ubuntu: install `postgresql-18`, cluster tooling `pg_lsclusters`/`pg_ctlcluster`, config, logs), dba-03 (backup/restore + PITR; creates a second cluster `restored` on port 5433; keeps basebackup + WAL archive on disk), dba-04 (pgbench init + workload, `pg_stat_statements`, verbose logging, pgBadger `-j 4`, pgCluu built from GitHub source).
- 40 GB disk exists for dba-03/04 headroom: live cluster + basebackup copy + WAL archive + pgbench DB + verbose logs ≈ 3× cluster size.
- Expected 17→18 demo-output deltas to watch for (verify, don't assume): initdb/package-install output now mentions data checksums (on by default in 18); every `postgresql-17` package/path/log string becomes `postgresql-18` / `/var/lib/postgresql/18/…`; psql banners 18.x; pgCluu/pgBadger PG-18 compatibility per the researcher's proposal.
