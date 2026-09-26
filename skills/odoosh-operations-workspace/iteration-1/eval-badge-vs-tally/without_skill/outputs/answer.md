# Why the odoo.sh build card says "test failed (de_fin_mail)" while install.log tallies 0 failed, 0 errors

## Short answer

The build card's status text and the pass/fail tally inside `install.log` are two
different measurements, produced by two different things. The card is odoo.sh's
own derived summary of the build — a status computed by scanning the log for
failure signatures and guessing which module(s) to name — while "0 failed, 0
errors" is one specific tally line written by Odoo's own test runner. They can
disagree, and when they do, the raw log is the one to trust, but only if you
read all of it, not just the one line you happened to find.

The module named in the card, de_fin_mail, is a known repeat offender on this
project: it has standing test failures that redden builds independently of
whatever change is actually being tested, and the card's module attribution for
those failures over-reports — it does not reliably name the module or test that
actually failed. That combination (a generic, over-inclusive badge message,
layered on top of a module with a pre-existing red history) is the most likely
explanation here, but it should be confirmed against this specific build's log,
not assumed.

## Why the mismatch happens

### 1. The card is a derived status, not a live re-query of the log

odoo.sh renders three build states for the install/test phase: success (green),
warning (orange — modules installed but at least one test failed, database
still usable), and failed (red — install/update itself raised an error, no
usable database). The short text under the badge ("At least one test failed
when loading the modules (...)") is a canned message template that odoo.sh's
own log-parsing layer fills in; it is not a direct quote of a single line in
the log, and it is not recomputed the instant you look at the log yourself. A
scan that ran once, early, or against a slightly different snapshot of the
output than what ended up in the final `install.log` can leave the card in a
state that a full read of the finished log no longer supports.

### 2. "0 failed, 0 errors" may be only one tally line among several

Odoo's test runner writes a pass/fail tally per module (and sometimes per
phase — install vs. update, or a base run followed by a retry). A build that
touches several modules, or that installs and then updates in the same run,
can contain more than one such tally line. Reading one "0 failed, 0 errors"
line and treating it as the verdict for the entire build is the classic trap:
the line you found may cover a different module, a different phase, or only
part of the run, while a FAIL or ERROR sits in a different block of the same
file. The only reliable check is to grep the whole log for every test result,
not to trust whichever tally line is easiest to find (e.g. the last one).

### 3. "failed when loading the modules" often points at load time, not test time

The phrase "when loading the modules" is significant: it is the wording odoo.sh
uses for problems encountered while a module is being installed/updated
(registry setup, a broken view, a demo-data record that fails validation, an
exception raised from a `_register_hook` or similar), which is a different
failure channel from the unittest pass/fail tally. A traceback or an
ERROR-level log line raised during loading can trip odoo.sh's failure
detector even though the unittest framework's own tally — the "X failed, Y
errors" you found — comes out clean, because that tally only counts tests
that the unittest runner actually executed and scored. A module named
de_fin_mail (a financial/mail-notification module, by the naming) is exactly
the kind of module where install-time side effects — e.g. an attempted mail
send or outgoing-connection check during install or demo-data loading — can
throw and get logged as an error without ever being recorded as a "failed
test."

### 4. Known standing condition on this project

Independent of the general mechanism above: de_fin_mail already has standing
test failures on this project that make builds show red regardless of the
change being tested — this is a pre-existing, previously-identified condition,
not necessarily something introduced by the commit behind this build. If this
build's log genuinely tallies 0 failed / 0 errors somewhere, two explanations
are both plausible and worth distinguishing: either this build happens to have
avoided the known failures (worth confirming, not assuming), or the "0 failed,
0 errors" you read is not the tally block that covers the known-bad tests —
i.e. explanation #2 above.

### 5. The card's module attribution over-reports

The parenthetical module list on the card is odoo.sh's attribution, not a
verified root cause. In practice it can list every module that was part of the
install/update batch (or that was loading around the point a failure signature
was seen), not specifically the module whose test failed. That means
de_fin_mail appearing in the message does not by itself prove any de_fin_mail
test failed — it may simply have been present in the same batch as whatever
module actually failed, or logged near the timestamp the detector keyed off
of. Do not treat the named module as a confirmed diagnosis; treat it as a
hint that needs verification against the log.

### 6. Lower-probability causes worth ruling out

- Stale dashboard render: the card is showing a cached status and a manual
  refresh of the page changes nothing meaningful — cheap to check first.
- Wrong build/log pairing: the install.log being read is not the log for the
  exact build the card belongs to (an old build, a rebuild, or a different
  commit on the same branch) — confirm the build number/commit hash and
  timestamp on both match.
- Phase split: at-install tests (`at_install=True`) and post-install tests
  (`post_install=True`) can run and report separately; a clean tally for one
  phase says nothing about the other.
- A flaky/order-dependent test that failed on a previous attempt but passed on
  this run, with the badge state left over from the earlier attempt rather
  than recomputed for this one.
- The build's overall exit status being driven by something other than the
  unittest tally (e.g. a non-zero process exit code from an unrelated error),
  which odoo.sh may still surface using its generic "test failed" wording.

## What to check, in order

1. Confirm the build identity: make sure the install.log you are reading and
   the card you are reading refer to the same build number/commit and the
   same timestamp — not an earlier or later build on the same branch.
2. Read the full install.log, not just the summary line: grep the entire file
   for `FAIL`, `ERROR`, `CRITICAL`, and `Traceback`, case-sensitive, rather
   than searching only for the final tally. Note every hit's timestamp and
   which module/test it falls under.
3. Enumerate tally lines: search for every occurrence of a pass/fail summary
   (there is often one per module and/or per phase) and confirm the "0
   failed, 0 errors" you found is the one that actually covers de_fin_mail's
   own tests, not a different module's or a different phase's.
4. Check specifically around where de_fin_mail is loading/installing (search
   for the module's own log lines) for exceptions or ERROR-level entries that
   occur outside the unittest tally altogether — e.g. during demo-data
   loading, a `_register_hook`, or an outgoing-mail/connection attempt made at
   install time. These would explain a "failed when loading the modules"
   message that never shows up as a counted test failure.
5. Check whether this failure signature matches the previously-identified
   standing de_fin_mail failures, or is new. If it matches the known
   condition, this build's red/warning status may be expected background
   noise rather than a regression from the current change.
6. Check the badge's exact color/state (warning vs. failed) — a "Warning"
   (tests failed but the database still installed and is usable) is a
   different situation from a hard "Failed" (module load itself broke, no
   usable database), even though both can generate a similarly worded
   message.
7. Look at modules adjacent to de_fin_mail in the install/update batch (its
   dependencies and dependents) — because the card's module list over-reports,
   the actual failing test may belong to a neighboring module that happened
   to be loading at the same time, not to de_fin_mail itself.
8. If still ambiguous, compare against another recent build's log for the
   same module to see whether the same signature appears there too (supports
   "known standing issue") or is unique to this build (supports "new
   regression tied to this change").

## Bottom line

Do not resolve this by trusting either side in isolation: not the card's
message (it is a derived, sometimes over-inclusive summary) and not a single
"0 failed, 0 errors" line (it may not be the tally block that matters here).
Resolve it by reading the complete install.log for this exact build, checking
for load-time exceptions in addition to unittest results, and cross-referencing
against the module's already-known standing failures before concluding
whether this is new or expected.
