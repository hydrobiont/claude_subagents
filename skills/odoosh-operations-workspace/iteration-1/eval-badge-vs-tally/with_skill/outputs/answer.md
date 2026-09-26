# Why the build card says "At least one test failed when loading the modules (de_fin_mail)" while `install.log` shows 0 failed, 0 errors

## What is going on

The status card and the test tally are **two independent signals computed from the same log by two different rules**, and they do not agree by design in this situation.

- The tally line (`odoo.tests.result: N failed, M error(s) of K tests`) is the test runner's own pass/fail count. `0 failed, 0 error(s)` means every test assertion in the run passed.
- The build card's status word, however, is **not** derived from that tally. odoo.sh marks a module as failed if **any ERROR-level line was logged while that module's tests were running** — full stop, regardless of what the test runner's own tally says. A test can pass every assertion and the module can still be flagged, because the badge is scanning log *severity*, not test *results*.

This is a confirmed, previously-seen case for this exact module. Build `38535645` (`de_fin_mail`, 2026-09-23) reported `0 failed, 0 error(s) of 190 tests` in `install.log`, with `de_fin_mail: 34 tests` all present and accounted for. The only ERROR-level lines anywhere in the log during that module's run were two lines that the module's **own guard methods logged on purpose** — each one exercised by a test that specifically asserts the guard fires (i.e., the test is *deliberately* triggering the error path to prove the guard works). Despite a perfectly clean tally, the build's status card still read "At least one test failed when loading the modules." That is the same wording given in this task, against the same module, so this is very likely the same class of failure recurring rather than a new problem.

Two secondary points worth carrying into the investigation:

1. The status card's own **failing-module list is separately unreliable** — on 2026-08-25 a build named a module in that list for which no test anywhere in the log had actually failed. So even the fact that the card names `de_fin_mail` specifically should be confirmed against the log, not taken on faith.
2. There is one **known benign false hit** to rule out before concluding anything: a line matching `<string>:NN: (ERROR/3) Unexpected indentation.` is `docutils` complaining about RST formatting inside a manifest's `description` field. It is pre-existing noise that appears on green builds too, and is unrelated to a module's actual guard/error-logging behavior — confirm any `ERROR` hit is *not* this exact shape before treating it as the cause.

## What to check

Work from `install.log` (the whole file, over SSH/Shell tab or the Logs tab scrolled to the top — the web viewer loads the tail first and a tail-only read silently drops earlier phases). Answer these as two **separate** questions; a clean answer to the first does not answer the second:

1. **Did the tests actually pass?**
   - Grep the overall tally: `grep -aE "odoo\.tests\.result:" install.log` → confirm it reads `0 failed, 0 error(s) of K tests`.
   - Grep the module's own count: `grep -aE "odoo\.tests\.stats: de_fin_mail:" install.log` → confirms `de_fin_mail`'s tests actually ran (e.g., `de_fin_mail: 34 tests`), not skipped or excluded.

2. **Is there an ERROR-level line during that module's run regardless of the tally?**
   - Grep `grep -a " ERROR " install.log` (the log-level token with surrounding spaces, not the word "error" appearing anywhere) and locate any hits that fall within `de_fin_mail`'s install/test window.
   - For each hit, pull ~20 lines of context and determine which of these it is:
     - A **deliberate** guard/logged-error that a test asserts on purpose (the confirmed-case pattern) — check whether the surrounding test explicitly expects this error (e.g., testing that invalid input is correctly rejected/logged).
     - The **docutils RST noise** pattern described above (benign, pre-existing, unrelated to this module's logic).
     - An actual, unasserted error that the test suite happens not to be checking for — this would be a real problem even though the tally reads clean, since the tally only reflects assertions the tests explicitly made.
   - The **View errors** panel on the build card is a convenience view of WARNING-and-above lines, but shows no tracebacks once the tally is clean — useful for a quick look, not a substitute for grepping the log directly.

3. **If this matches the confirmed pattern** (a deliberate, asserted, on-purpose ERROR-level log line from a guard method, with the tally otherwise clean): the documented fix is to wrap the deliberate error-producing call in the test with `self.assertLogs("<logger>", level="ERROR")`. This both keeps the assertion that the line fired (no loss of coverage) and captures/suppresses the line so odoo.sh's badge scanner never sees it at ERROR level in `install.log`. That was the exact fix applied in commit `025af82` for the earlier `de_fin_mail` occurrence, after which the rebuilt badge went green. If a fresh occurrence is confirmed to be the same shape, the same pattern applies to whichever guard method(s) are now producing the ERROR-level line.

## Bottom line

Do not call this build "failed" or "broken" from the card alone. `Test: Warning` with sub-status `done` is this project's normal healthy result, and a `Test: Failed` badge naming `de_fin_mail` has already been shown, on this exact module, to co-exist with a perfectly clean `0 failed, 0 error(s)` tally — caused by intentional ERROR-level guard logging that odoo.sh's pass/fail badge does not distinguish from a real failure. The next step is to grep the whole `install.log` for ` ERROR ` lines inside `de_fin_mail`'s run and classify each one (deliberate-and-asserted vs. docutils noise vs. genuinely unasserted) before deciding whether anything actually needs fixing.
