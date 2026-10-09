---
name: monthly-statements
description: >-
  Monthly bookkeeping run for Data Egret GmbH: collect the month's financial documents and file
  them on the accounting shared drive under statements/<YEAR>/<MM>/ (one folder per month), every
  document in the month its OWN dates cover. Sources: the Bank 1 Saar mailbox export
  (Kontoauszug of account 124536006 and the Mastercard statements, provided by the user), American
  Express Business Platinum (statement PDF and CSV), the Wise business account (EUR, GBP and USD
  monthly statements, PDF and CSV, fees as separate lines) and the Stripe LIVE account (fee tax
  invoice, customer invoices, balance summary PDF and CSV, itemised activity CSV, fees CSV). Use
  when the user asks to "do the monthly statements", "collect / sort / file the statements for
  <month>", "prepare the documents for the accountant / Steuerberater / Buchhaltung", "download
  the Stripe / Wise / Amex statements", "clean up the statements folder", or drops PostfachDokumente
  or statement zips into the statements folder. Bundled tool: scripts/statements.py (plan, apply,
  place, retire-multi, check, tree). Every Drive write and every Stripe export needs the user's
  explicit confirmation first.
---

# Monthly statements (Data Egret GmbH)

The deliverable is a plain tree of `statements/<YEAR>/<MM>/` in which every account has, per
month, a PDF to check and a CSV to import into the accounting system. The user set the rules
below on 2026-09-29, when the first run sorted January to August 2026.

Drive root: `~/Library/CloudStorage/GoogleDrive-ik@dataegret.com/Shared drives/accounting/data_egret_gmbh/statements`
Tool: `TOOL=~/.claude/skills/monthly-statements/scripts/statements.py` (Python 3 standard
library, needs `pdftotext`; every subcommand is a dry run until `--apply`; `--help` lists them).

## Rules the user set

1. **No write without confirmation.** Show the dry-run plan and what will be downloaded, then
   ask once; the confirmation covers exactly the listed operations. Stripe report exports create
   report runs, so they are part of that confirmation. On Stripe nothing else is allowed: no
   settings, no Schedule, no refunds, invoices, payouts or Sigma.
2. **Only the year folder of the month being processed.** A document dated in another year stays
   where it is and is reported. Example: the American Express statement dated 2 January covers
   December of the previous year.
3. **File by the document's own dates**, never by file name, download date or current folder
   (rules in `references/document-types.md`).
4. **Unpack source archives** (the bank's `PostfachDokumente_*.zip`, Wise's
   `statement_<from>_<to>_pdf|csv.zip`) and trash them once every member is filed. Any other
   archive (for example an `Archive.zip` the user made for the accountant) is never trashed.
5. **Keep duplicates**: PDF and CSV of the same statement, and re-downloaded copies, sit side by
   side. Only a byte-identical file of the same name collapses to one copy. A same-name file
   with different content is never overwritten; the tool stops instead.
6. **Wise statements show fees as separate lines** ("Display transactions with fees shown
   separately"), like every statement the user downloads by hand; that is how the exchange fees
   become visible. A folded-fee statement is replaced.
7. Deleting on the Drive mount moves the item to the shared drive's trash (30 days).

## When to run

After the 5th of the following month: Stripe issues the fee tax invoice around the 5th, the bank
statement and Mastercard statements arrive in the bank mailbox at the start of the month, and
the American Express statement closes on the 2nd. Default month: the previous calendar month.
Also run `check` over earlier months; late documents show up as gaps there.

## Procedure

0. **Set up.** `Y=<year>; M=<MM>; STAGE=<session scratchpad>/statements-$Y-$M`. Take a local
   backup before any write: `cp -Rp "<root>/$Y" "$STAGE/backup-before"`.
1. **Ask the user for the bank files.** They download the mailbox export
   (`PostfachDokumente_*.zip`: Kontoauszug and Mastercard statements) from Bank 1 Saar online
   banking and drop it, plus anything else they already have (American Express files, Wise
   files), anywhere in `statements/$Y/`.
2. **Inventory, read-only.** Run `$TOOL plan --year $Y` and `$TOOL check --year $Y --month $M`.
   Note the gaps: which sources still need a download.
3. **One confirmation** (AskUserQuestion), listing:
   - the Drive operations from the plan (moves, extractions, trash), with counts;
   - the downloads (Wise statements, American Express statement and CSV, Stripe invoices and
     exports), naming the Stripe report runs;
   - which sign-ins the user will do in the visible browser window.
4. **Browser work**, one `browser-operator` agent at a time on `playwright-persistent-ui`, using
   the briefs in `references/agent-briefs.md`. Two agents on the one window fight over the
   current tab, so never run them in parallel.
   - Order: Wise, then American Express, then Stripe. Wise and Amex sessions time out quickly,
     so each runs right after its sign-in; the Stripe login (Google plus security key) lasts.
   - Each agent stages into `$STAGE/<source>/` and never writes to the Drive.
   - Existing PDFs (Stripe tax and customer invoices) are pure reads and may start before the
     confirmation; exports may not.
5. **File everything**, each step as a dry run first, then with `--apply`:
   - `$TOOL apply --year $Y`
   - `$TOOL place --year $Y --from "$STAGE/<source>"` for every staging folder
   - `$TOOL retire-multi --year $Y` when the plan flagged multi-month Wise statements. It trashes
     them only if the monthly CSVs reproduce their rows exactly.
6. **Verify.** `$TOOL check --year $Y` must report `0 problem(s)`. It covers misplaced files,
   folded Wise fees, Wise opening balance equal to the previous closing, and the PDF closing
   equal to the CSV closing. Remaining `GAP` lines go to the user as open items.
7. **Deliver** `$TOOL tree --year $Y --month $M` (or the whole year) as a plain tree in a code
   block. Add: what was added, the flags (other-year documents, kept archives), open gaps, and
   what went to trash.

## Traps seen on the first run

- **Browser tool auto-update.** The MCP servers run `@playwright/mcp@latest`. After a release,
  every newly launched browser fails with `Browser "chrome-for-testing" is not installed …
  chromium-NNNN`. Fix: in the newest `~/.npm/_npx/<dir>` holding `@playwright/mcp`, run
  `./node_modules/.bin/playwright-mcp install-browser --no-remove chromium`. Without
  `--no-remove` it deletes the build running browsers use. Then the user runs `/mcp` and chooses
  Reconnect for `playwright-persistent-ui`. The new window is a fresh vault clone, so Stripe,
  Wise and Amex need signing in again.
- **Safety check on deletions.** `rm` with a shell variable in the path is blocked by a safety
  check. Use the tool, which deletes through Python, or literal paths.
- **Classifier refusals.** The auto-mode classifier can refuse a single click (the Stripe payouts
  export was refused as "PII Data Handling" when the brief said no downloads). The agent lists
  it and moves on; the user clicks it if needed.
- **Stripe receipts.** On the Stripe invoices list, "Download PDF" can serve a receipt
  (`Receipt-*.pdf`). Download from the invoice's detail page; `check` flags stray receipts.
- **Stripe fee file names.** Fee export names are shifted one day earlier than the calendar month
  (Stripe pivots on the balance transaction date); the tool files them by majority of days.
- **Months without Stripe activity** have no itemised export and a header-only fees CSV. The
  balance summary documents the zero month.
- **Wise USD** is dormant: its CSVs are header-only; the PDF still prints the balance.

## Accounts (identifiers only; no secrets live here)

- Bank 1 Saar eG, account 124536006 (Stripe payouts land here). Mastercard statements for cards
  ending 032, 040, 394, 402 and 931; a card gets a statement only in months with activity.
- American Express Business Platinum, card ending 51000, holder Ilya Kosmodemiansky.
- Wise business account "Data Egret": EUR balance 20974321, GBP 20974432, USD 86561103.
- Stripe LIVE account `acct_1RWaJNAT35bH1mGW`. Payouts are manual, so Stripe offers no
  per-payout reconciliation report.

## Status

- 2026-09-29, first run: January to August 2026 filed and verified.
- 2026-10-01, September run: Wise, Stripe and the bank filed (the user dropped the bank's
  PostfachDokumente zip into 09 later that day; statement Nr.009 and Mastercard 040 and 394).
  September had no Stripe activity (zero balance, no invoices, no payouts, empty fees export, so
  no fee tax invoice is expected). American Express is added by the user.
- Still open: American Express CSVs for the January to April periods, statement PDFs for the May
  and June periods, and the September statement and CSV. The Amex brief is not yet proven; confirm its
  export options on its first run.
- Stripe's fee data posts with a 96-hour lag: the fees export of a month is complete only from
  about the 5th of the next month, which is one more reason to run after the 5th.
