# Browser agent briefs (templates)

Dispatch each as a `browser-operator` agent (model sonnet), one at a time, after the user's
confirmation. Replace `<Y>`, `<MM>`, `<first>`/`<last>` (first and last day of the month) and
`<STAGE>` (the run's staging folder in the session scratchpad). The Wise and Stripe briefs are
proven (2026-09-29); the American Express brief has not completed a run yet.

## Common block (paste into every brief)

> Server `playwright-persistent-ui` (visible window, tools `mcp__playwright-persistent-ui__*`).
> The user IS at the keyboard: open your own tab; if a login, code or security-key screen
> appears, WAIT for the user in that tab (`browser_wait_for`, re-check every minute, up to 15
> minutes; never type credentials or codes). Never touch, reload or close a tab you did not open;
> close only your own tab at the end. Downloads land in the Playwright MCP download location
> (see the tool result, usually `~/work/de/website/de-website-3/.playwright-mcp/`, spaces turned
> into dashes): copy each file with its real name into `<STAGE>/<source>/`. Never write to Google
> Drive. If the permission system refuses a click, do not retry and do not look for another
> route: list it and continue. Report a table of every staged file with name, size and `md5 -q`.

## Wise (proven)

> Wise Business, account "Data Egret" (check the account chip). READ-ONLY: no transfers,
> conversions, recipients, cards or settings; only statement generation and download. Use the
> statement wizard at https://wise.com/balances/statements/balance-statement/create, not the
> "Download" button on a currency page (that is a watermarked transaction history).
> For <MM>/<Y>, generate TWO statements, one PDF and one CSV:
> - period <first> to <last> (for the previous month the "Last month" radio fills it; otherwise
>   the calendar's year view reaches a month quickly);
> - currencies "Select all" (EUR 20974321, GBP 20974432, USD 86561103). Wise delivers a zip with
>   one file per currency;
> - format PDF, then CSV;
> - language German. It resets to English (UK) whenever the format radio changes, so set German
>   after choosing the format;
> - "Display transactions with fees shown separately" TICKED; "Stamp and sign" unticked.
> The checkboxes are hidden inputs; click their labels. Confirm on the "Statement summary" screen
> (fees shown separately: yes, language German) before "Download statement". Unzip into
> `<STAGE>/wise/`. Report, for each CSV, the number of rows whose "TransferWise ID" starts with
> `FEE-`. The field is unquoted in data rows.

## American Express (not yet proven)

> americanexpress.de, Business Platinum card ending 51000 (holder Ilya Kosmodemiansky); log in
> at https://www.americanexpress.com/de-de/account/login ("Kontotyp: Kartenkonto verwalten").
> READ-ONLY: no payments, card settings, disputes, paperless or address changes.
> For the statement dated 02.<MM+1>.<Y> (period 03.<MM>.–02.<MM+1>.):
> 1. The statement PDF ("Monatsabrechnung"), saved as `<Y>-<MM+1>-02.pdf`.
> 2. The transaction export as CSV for that statement period, with columns Datum, Beschreibung
>    and Betrag, without the optional additional details. Select the statement period in the
>    export dialog, not a free date range. Save it as `amex_activity_02.<MM+1>.<YY>.csv`.
> Before the first export, report the dialog options verbatim. Verify the PDF's
> "Abrechnungszeitraum vom … bis …" with pdftotext and the CSV's first and last row dates.
> Stage into `<STAGE>/amex/`.

## Stripe (proven)

> LIVE Stripe Dashboard of Data Egret GmbH (`acct_1RWaJNAT35bH1mGW`). Confirm LIVE mode first:
> no test or sandbox label and no `/test/` in any URL. The user approved report EXPORTS for
> <MM>/<Y>: an export creates a report run and changes nothing else. Nothing else is approved:
> no settings, no "Schedule…", no create, cancel, refund, void or send, no Sigma, no payouts.
> Stage everything into `<STAGE>/stripe/`.
>
> 1. **Fee tax invoice.** Settings → Plans and fees → Invoice history
>    (https://dashboard.stripe.com/acct_1RWaJNAT35bH1mGW/settings/plans-and-fees/invoice-history).
>    Row "Tax Invoice for <Month> <Y>" → "…" → Download. Stripe issues it around the 5th of the
>    following month; a month without fees has none.
> 2. **Customer invoices issued in <MM>/<Y>.** Invoices list
>    (https://dashboard.stripe.com/acct_1RWaJNAT35bH1mGW/invoices). For each invoice created in
>    the month, open its DETAIL page and use "Download PDF" there
>    (`download-invoice-pdf-button`, next to the hosted-invoice link). The list page's row
>    action can silently serve the receipt instead.
> 3. **Balance summary**, PDF and CSV. Open
>    https://dashboard.stripe.com/acct_1RWaJNAT35bH1mGW/reports/balance?startDate=<first>&endDate=<last>&currency=eur&templateType=merchant&timezone=Europe%2FBerlin
>    and wait until "Loading report…" disappears. Check the Date range control reads the month
>    and the timezone reads Europe/Berlin. Then use the "Balance summary" section's Export →
>    "Download to system", format CSV, then PDF, with default columns.
> 4. **Itemised balance change from activity.** At
>    https://dashboard.stripe.com/acct_1RWaJNAT35bH1mGW/reports/balance/activity-breakdown for
>    the same range, Export with column mode "Default (9)". The export is absent when the month
>    had no activity: report "no data".
> 5. **Fees.** At https://dashboard.stripe.com/acct_1RWaJNAT35bH1mGW/settings/plans-and-fees/fees
>    for the same month, Export → "Download to system", report format "Summary"; this produces a
>    CSV. Stripe names it with a range shifted one day earlier; keep the name. Fee data posts
>    with a 96-hour lag, so before the 5th the export is incomplete. The first Download click
>    sometimes does nothing; retry once.
>
> Keep Stripe's own file names. Report the balance summary's starting and ending balance as
> shown on screen.
