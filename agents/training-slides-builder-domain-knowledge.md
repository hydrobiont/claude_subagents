# Training Slides Builder — Domain knowledge

Persistent notes accumulated by the `training-slides-builder` agent across invocations. The agent reads this file at the start of every run and appends entries when it learns something durable about the domain — e.g. Reveal.js / markdown-converter pipeline quirks, recurring build-error patterns and their fixes, media-path conventions that aren't enforced by the toolchain, structural gotchas in theory.md / demo.md, etc.

See the agent definition (`training-slides-builder.md`) for the rules on what belongs here vs not.

<!-- entries below; newest on top -->

### Title date lives in common/global.md; version lives in headers — keep them in sync

The title-slide date renders from `common/global.md` `date: <Month YYYY>` — a single shared value across ALL decks (dev + dba), NOT from each header's `version:` field. They must be kept consistent by hand: version `2026.6` ⇒ date `June 2026`. A stale `date:` (e.g. `October 2025` left from a prior release) silently brands every built deck — slides and handouts — with the wrong month. Static check 7 cross-checks `global.md` `date:` against the build's `header.md` `version:`. Caveat: editing `global.md` changes the date for every track, so confirm the value suits the whole catalogue before building.

### Handout strips trainer-only preambles via scripts/strip-handout.awk

Demo files open with trainer-only setup (gcloud SSH + `sudo -u postgres` login to `stg-devpg-01-gcp-instance01`, tunnel connection strings) that must not reach trainees. Each marks the end of that block with `<!-- the part above is to be removed later for handouts -->` (or "...handovers"). The Makefile concatenation runs every source file through `scripts/strip-handout.awk`, which — when the marker is present — drops everything up to AND including it; files without the marker pass through unchanged. Only handouts are affected (the slides build already filters out `*demo.md`). Two failure modes to flag: (a) a demo with trainer login but NO marker (static check 8) → it leaks; (b) a marker whose wording doesn't match the awk regex `to be removed.*for hand(over|out)s`. Verify with the Phase-4 handout grep — expect 0 hits for `gcloud compute ssh|sudo -u postgres|stg-devpg-01`.

### Closing code fences are not missing language tags

The static check for "code fence missing language tag" must skip lines that match exactly ` ``` ` (the closing fence). Only opening fences — lines starting with ` ``` ` followed by a non-empty language identifier — need tagging. Flagging bare ` ``` ` lines is a false positive.

### Overflow check: Reveal getBoundingClientRect is reliable at 1440×900

Running `getBoundingClientRect()` on all `slide.querySelectorAll('*')` elements after `reveal.slide(i)` + a 120 ms pause gives accurate overflow detection. The 2 px tolerance avoids sub-pixel rounding false positives. This approach worked cleanly on dev-01 (17 slides, zero overflows).

### HTTP server port convention for visual overflow checks

Use port 8791 for the local Python HTTP server during overflow checks (`python3 -m http.server 8791 --bind 127.0.0.1`). Avoids conflicts with common dev ports.
