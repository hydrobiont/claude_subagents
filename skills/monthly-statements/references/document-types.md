# Document types and how their month is decided

`scripts/statements.py` implements exactly these rules (`classify()`). Read the period from the
document itself; file names and folders are only hints.

| Source | Typical file name | Period read from | Filed under |
|---|---|---|---|
| Bank 1 Saar account statement | `124536006_<Y>_Nr.NNN_Kontoauszug_vom_<date>_<stamp>.pdf` | "neuer Kontostand vom DD.MM.YYYY" | month of the closing date (the "vom" date in the name is the issue date, one month later) |
| Bank 1 Saar Mastercard statement | `XXXXXXXXXXXXX<card>_<Y>_Kreditkarten-Umsatzaufstellung_vom_<date>_<stamp>.pdf` | "Abrechnungsdatum: DD.MM.YYYY" | billing month, even when "Umsatzaufstellung vom … bis …" spans several months |
| Bank mailbox export | `PostfachDokumente_<stamp>.zip` | members | unpacked; the zip goes to trash |
| American Express statement | `YYYY-MM-DD.pdf` (statement date, the 2nd) | "Abrechnungszeitraum vom 03.MM.YY bis 02.MM.YY" | month holding most of the period, i.e. the month BEFORE the file name; the January statement covers December of the previous year |
| American Express CSV | `activity*.csv`, `amex_activity_DD.MM.YY.csv` | header `Datum,Beschreibung,Betrag`, row dates DD/MM/YYYY | month holding most rows (period 3rd to 2nd) |
| Wise statement | `statement_<balance id>_<CUR>_<from>_<to>.pdf/.csv` | the from/to dates in the name (the PDF text repeats them) | that month; a multi-month file is superseded by monthly ones (`retire-multi`) |
| Wise download | `statement_<from>_<to>_pdf.zip` / `_csv.zip` | members | unpacked; the zip goes to trash |
| Stripe fee tax invoice | `Stripe Tax Invoice 35BH1MGW-<Y>-<MM>.pdf` | "Service Month Mon YYYY" | service month |
| Stripe customer invoice | `Invoice-5ILRFKDD-NNNN.pdf` | "Date of issue …" (two date formats occur) | month of issue |
| Stripe receipt (unwanted) | `Receipt-NNNN-NNNN.pdf` | — | not filed; fetch the invoice PDF instead |
| Stripe balance summary PDF | `balance_summary_<Mon>-1-<Y>_<Mon>-<D>-<Y>_EUR_summary.pdf` | range in the name | that month |
| Stripe balance summary CSV | `Balance_Summary_EUR_<from>_to_<to>_Europe-Berlin.csv` | range in the name | that month |
| Stripe itemised activity CSV | `Itemized_balance_change_from_activity_EUR_<from>_to_<to>_Europe-Berlin.csv` | range in the name | that month (absent in months without activity) |
| Stripe fees CSV | `All_fees_summary_pivoted_on_balance_transaction_date_EUR_<from>_to_<to>.csv` | range in the name, shifted one day earlier | month holding most of the range |
| Stripe balance page print | `Balance – Data Egret GmbH – Stripe.pdf` (older manual prints) | "Mon 1, YYYY" in the text | that month |

Anything else is left where it is and reported as `unrecognised`. Add a new type to `classify()`
and to this table in the same change.

Month folders are two digits (`01` … `12`). The year folder holds nothing but month folders,
apart from archives the user keeps on purpose.
