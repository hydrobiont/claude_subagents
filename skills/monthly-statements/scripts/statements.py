#!/usr/bin/env python3
"""statements.py - sort Data Egret GmbH's monthly financial statements into statements/<YEAR>/<MM>/.

Every document is filed under the month its OWN dates cover (read from the PDF text or CSV rows),
never by its file name, download date or current folder. Python 3 standard library + pdftotext.

Subcommands (read-only unless --apply is given):
  plan         --year Y                  classify every file and zip member under <root>/<Y>; print the operations
  apply        --year Y --apply          do it: move loose files, extract zip members, trash placed zips and
                                         byte-identical same-name copies (Drive for desktop sends deletions to the
                                         shared drive's trash, restorable for 30 days)
  place        --year Y --from DIR [--apply]   copy staged downloads (files or zips) into their month
  retire-multi --year Y [--apply]        trash multi-month Wise statements (loose or zipped) once the monthly CSVs
                                         reproduce their rows exactly
  check        --year Y [--month MM]     misplaced files, Wise PDF+CSV per currency, separate fee lines, balance
                                         continuity (opening = previous closing), per-month inventory and gaps
  tree         --year Y [--month MM]     plain tree of the year (or one month)

Rules the tool enforces: nothing is ever overwritten (a same-name file with different content stops the run
before any write); a document dated in another year is left where it is and flagged; unknown files are left
alone and reported; .DS_Store is ignored.
"""
import argparse, collections, csv, datetime as dt, hashlib, io, os, re, shutil, subprocess, sys, zipfile
from decimal import Decimal

DEFAULT_ROOT = os.path.expanduser(
    "~/Library/CloudStorage/GoogleDrive-ik@dataegret.com/Shared drives/accounting/data_egret_gmbh/statements")
EN = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
DE = {"Januar": 1, "Februar": 2, "März": 3, "April": 4, "Mai": 5, "Juni": 6, "Juli": 7, "August": 8,
      "September": 9, "Oktober": 10, "November": 11, "Dezember": 12}
WISE_ACCOUNTS = {"EUR": "20974321", "GBP": "20974432", "USD": "86561103"}

md5 = lambda b: hashlib.md5(b).hexdigest()

def pdf_text(data, first_page_only=False):
    cmd = ["pdftotext", "-layout"] + (["-l", "1"] if first_page_only else []) + ["-", "-"]
    try:
        out = subprocess.run(cmd, input=data, capture_output=True, timeout=60).stdout.decode("utf-8", "replace")
    except FileNotFoundError:
        sys.exit("pdftotext is required (brew install poppler)")
    return re.sub(r"[ \t]+", " ", out)

def majority_month(a, b):
    c, d = collections.Counter(), a
    while d <= b:
        c[(d.year, d.month)] += 1; d += dt.timedelta(days=1)
    return c.most_common(1)[0][0]

def classify(name, data):
    """-> (kind, target, reason); target = (year, month) | 'MULTI' | None."""
    n, low = name, name.lower()
    if low.endswith(".csv"):
        t = data.decode("utf-8", "replace")
        m = re.match(r"statement_(\d+)_([A-Z]{3})_(\d{4})-(\d\d)-(\d\d)_(\d{4})-(\d\d)-(\d\d)\.csv$", n)
        if m:
            return wise(m, "csv")
        if t.startswith("Datum,Beschreibung,Betrag"):
            ds = [dt.date(int(y), int(mo), int(d)) for d, mo, y in re.findall(r"^(\d\d)/(\d\d)/(\d{4}),", t, flags=re.M)]
            if not ds: return "amex_csv", None, "Amex CSV without rows"
            c = collections.Counter((x.year, x.month) for x in ds)
            return "amex_csv", c.most_common(1)[0][0], f"Amex CSV, {len(ds)} rows {min(ds):%d.%m.%Y}-{max(ds):%d.%m.%Y}"
        for prefix, kind in (("Balance_Summary_", "stripe_balance_csv"),
                             ("Itemized_balance_change_from_activity_", "stripe_itemised_csv"),
                             ("All_fees_", "stripe_fees_csv")):
            if n.startswith(prefix):
                r = re.search(r"(\d{4})-(\d\d)-(\d\d)_to_(\d{4})-(\d\d)-(\d\d)", n)
                a = dt.date(*map(int, r.groups()[:3])); b = dt.date(*map(int, r.groups()[3:]))
                return kind, majority_month(a, b), f"Stripe export {a}..{b}"
        return "unknown", None, "unrecognised CSV"
    if not low.endswith(".pdf"):
        return "unknown", None, "not a PDF/CSV"
    m = re.match(r"statement_(\d+)_([A-Z]{3})_(\d{4})-(\d\d)-(\d\d)_(\d{4})-(\d\d)-(\d\d)\.pdf$", n)
    if m:
        return wise(m, "pdf")
    t = pdf_text(data)
    if "Kontoauszug" in n or "neuer Kontostand vom" in t:
        r = re.search(r"neuer Kontostand vom (\d\d)\.(\d\d)\.(\d{4})", t)
        if r: return "bank", (int(r.group(3)), int(r.group(2))), f"bank statement, closing {r.group(1)}.{r.group(2)}.{r.group(3)}"
    if "Kreditkarten-Umsatzaufstellung" in n or "Umsatzaufstellung vom" in t:
        r = re.search(r"Abrechnungsdatum: (\d\d)\.(\d\d)\.(\d{4})", t)
        p = re.search(r"Umsatzaufstellung vom ([\d.]+) bis ([\d.]+)", t)
        if r: return "mastercard", (int(r.group(3)), int(r.group(2))), \
            f"Mastercard {n[13:16] if n.startswith('XXXX') else ''} billing {r.group(1)}.{r.group(2)}.{r.group(3)}" + (f" (period {p.group(1)}-{p.group(2)})" if p else "")
    if "American Express" in t:
        r = re.search(r"Abrechnungszeitraum vom (\d\d)\.(\d\d)\.(\d\d) bis (\d\d)\.(\d\d)\.(\d\d)", t)
        if r:
            a = dt.date(2000 + int(r.group(3)), int(r.group(2)), int(r.group(1)))
            b = dt.date(2000 + int(r.group(6)), int(r.group(5)), int(r.group(4)))
            return "amex_pdf", majority_month(a, b), f"Amex statement {a:%d.%m.%Y}-{b:%d.%m.%Y}"
    if n.startswith("Stripe Tax Invoice"):
        r = re.search(r"Service Month (\w{3}) (\d{4})", t)
        if r: return "stripe_tax_invoice", (int(r.group(2)), EN[r.group(1)]), f"Stripe fee tax invoice, service month {r.group(1)} {r.group(2)}"
    if n.startswith("Invoice-"):
        r = re.search(r"Date of issue (\w+) (\d+), (\d{4})", t) or re.search(r"Date of issue (\d+) (\w+) (\d{4})", t)
        if r:
            mon = r.group(1) if r.group(1).isalpha() else r.group(2)
            return "stripe_invoice", (int(r.group(3)), EN[mon[:3]]), f"customer invoice, issued {r.group(1)} {r.group(2)} {r.group(3)}"
    if n.startswith("Receipt-"):
        return "stripe_receipt", None, "Stripe RECEIPT, not an invoice: re-download the invoice PDF from the invoice's detail page"
    if n.startswith("balance_summary_"):
        r = re.search(r"_(\w{3})-(\d+)-(\d{4})_(\w{3})-(\d+)-(\d{4})_", n)
        if r:
            a = dt.date(int(r.group(3)), EN[r.group(1)], int(r.group(2))); b = dt.date(int(r.group(6)), EN[r.group(4)], int(r.group(5)))
            return "stripe_balance_pdf", majority_month(a, b), f"Stripe balance summary PDF {a}..{b}"
    if n.startswith("Balance") and "Stripe" in n:
        r = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) 1, (\d{4})", t)
        if r: return "stripe_balance_print", (int(r.group(2)), EN[r.group(1)]), f"Stripe balance report (browser print), {r.group(1)} {r.group(2)}"
    return "unknown", None, "unrecognised PDF"

def wise(m, ext):
    a = dt.date(int(m.group(3)), int(m.group(4)), int(m.group(5))); b = dt.date(int(m.group(6)), int(m.group(7)), int(m.group(8)))
    kind = f"wise_{ext}"
    if (a.year, a.month) == (b.year, b.month):
        return kind, (a.year, a.month), f"Wise {m.group(2)} {ext.upper()} {a}..{b}"
    return kind, "MULTI", f"Wise {m.group(2)} {ext.upper()} spanning {a}..{b} (superseded by monthly statements)"

# ---------------------------------------------------------------------------------------------- planning
class Plan:
    def __init__(self, ydir, year):
        self.ydir, self.year = ydir, year
        self.ops, self.conflicts, self.flags = [], [], []
        self.placed = {}          # (folder, name) -> md5

    def folder_for(self, tgt):
        if tgt is None or tgt == "MULTI": return None
        y, m = tgt
        return f"{m:02d}" if y == self.year else f"OTHER-YEAR {y}-{m:02d}"

    def target_state(self, folder, name):
        """md5 of what will sit at folder/name after the ops so far (None if nothing)."""
        if (folder, name) in self.placed: return self.placed[(folder, name)]
        p = os.path.join(self.ydir, folder, name)
        return md5(open(p, "rb").read()) if os.path.exists(p) else None

    def add_file(self, src_rel, name, data, origin, zpath=None):
        kind, tgt, why = classify(name, data)
        folder = self.folder_for(tgt)
        cur = os.path.dirname(src_rel) if origin == "loose" else None
        if folder is None:
            self.flags.append((src_rel, why)); return "flag"
        if folder.startswith("OTHER-YEAR"):
            self.flags.append((src_rel, f"{why}: belongs to {folder[11:]}, left where it is (only {self.year} is touched)")); return "flag"
        existing = self.target_state(folder, name)
        h = md5(data)
        if origin == "loose" and cur == folder:
            self.placed[(folder, name)] = h; return "stay"
        if existing is not None:
            if existing == h:
                if origin == "loose": self.ops.append(("TRASH", src_rel, folder, f"byte-identical copy already in {folder}/"))
                else: self.ops.append(("SKIP", src_rel, folder, f"identical file already in {folder}/"))
                return "dup"
            self.conflicts.append((src_rel, folder, name)); return "conflict"
        self.placed[(folder, name)] = h
        if origin == "loose":
            self.ops.append(("MOVE", src_rel, folder, why))
        else:
            self.ops.append(("EXTRACT", src_rel, folder, why, (zpath, name)))
        return "place"

SOURCE_ARCHIVE = re.compile(r"^(PostfachDokumente_.*|statement_\d{4}-\d\d-\d\d_\d{4}-\d\d-\d\d_(pdf|csv))\.zip$")

def skip_name(path):
    b = os.path.basename(path)
    return b == ".DS_Store" or b.startswith("._") or "__MACOSX/" in path

def iter_year(ydir):
    for r, ds, fs in os.walk(ydir):
        ds.sort()
        for f in sorted(fs):
            if skip_name(f): continue
            yield os.path.join(r, f)

def build_plan(ydir, year):
    pl = Plan(ydir, year)
    loose = [p for p in iter_year(ydir) if not p.lower().endswith(".zip")]
    zips = [p for p in iter_year(ydir) if p.lower().endswith(".zip")]
    for p in loose:
        rel = os.path.relpath(p, ydir)
        pl.add_file(rel, os.path.basename(p), open(p, "rb").read(), "loose")
    for z in zips:
        rel = os.path.relpath(z, ydir); results = []
        with zipfile.ZipFile(z) as zf:
            for zi in zf.infolist():
                if zi.is_dir() or skip_name(zi.filename): continue
                results.append(pl.add_file(f"{rel} :: {zi.filename}", os.path.basename(zi.filename), zf.read(zi), "zip", z))
        if not SOURCE_ARCHIVE.match(os.path.basename(z)):
            pl.flags.append((rel, f"not a bank or Wise download: kept; {results.count('dup')} of {len(results)} members already filed"
                                  + (f", {results.count('place')} new ones extracted" if results.count('place') else "")))
        elif all(r in ("place", "dup") for r in results):
            pl.ops.append(("TRASH", rel, None, "all members placed"))
        else:
            pl.flags.append((rel, "zip kept: holds members that are not placed (see flags above)"))
    return pl

def print_plan(pl):
    for op in pl.ops:
        print(f"{op[0]:8s} {op[1]}" + (f"  ->  {op[2]}/" if op[2] else "") + f"   [{op[3]}]")
    for src, why in pl.flags: print(f"FLAG     {src}   [{why}]")
    for src, folder, name in pl.conflicts: print(f"CONFLICT {src} -> {folder}/{name} exists with different content")
    c = collections.Counter(o[0] for o in pl.ops)
    print(f"\n{sum(c.values())} operations: " + ", ".join(f"{k} {v}" for k, v in sorted(c.items())) +
          f"; {len(pl.flags)} flags; {len(pl.conflicts)} conflicts")

def execute(pl, ydir):
    if pl.conflicts: sys.exit("conflicts present: nothing written")
    for op in pl.ops:
        kind, src, folder = op[0], op[1], op[2]
        if kind == "MOVE":
            os.makedirs(os.path.join(ydir, folder), exist_ok=True)
            os.rename(os.path.join(ydir, src), os.path.join(ydir, folder, os.path.basename(src)))
        elif kind == "EXTRACT":
            zpath, name = op[4]
            os.makedirs(os.path.join(ydir, folder), exist_ok=True)
            with zipfile.ZipFile(zpath) as zf:
                member = src.split(" :: ", 1)[1]
                with open(os.path.join(ydir, folder, name), "wb") as fh: fh.write(zf.read(member))
        elif kind == "TRASH":
            os.remove(os.path.join(ydir, src))
        else:
            continue                            # SKIP: nothing to do, nothing to report
        print(f"done {kind:8s} {src}")
    remove_empty_dirs(ydir)

def remove_empty_dirs(ydir):
    for d in sorted(os.listdir(ydir)):          # remove folders left empty (apart from .DS_Store)
        p = os.path.join(ydir, d)
        if os.path.isdir(p) and not [f for f in os.listdir(p) if f != ".DS_Store"]:
            ds = os.path.join(p, ".DS_Store")
            if os.path.exists(ds): os.remove(ds)
            os.rmdir(p); print(f"done RMDIR    {d}/ (empty)")

# ---------------------------------------------------------------------------------------------- Wise checks
def wise_rows(text):
    return list(csv.DictReader(io.StringIO(text)))

def parse_amount(s):
    s = s.strip()
    if re.search(r",\d\d$", s): s = s.replace(".", "").replace(",", ".")
    else: s = s.replace(",", "")
    return Decimal(s)

def wise_pdf_closing(data, cur):
    t = pdf_text(data, first_page_only=True)
    r = re.search(rf"{cur} (?:am|on) \d+\.? \w+ \d{{4}} \[GMT[^\]]*\] (-?[\d.,]+) {cur}", t)
    return parse_amount(r.group(1)) if r else None

def retire_multi(ydir, year, apply):
    """Multi-month Wise files (loose or in zips) whose rows the monthly CSVs reproduce exactly."""
    def is_multi_csv(b):
        return bool(re.match(r"statement_\d+_[A-Z]{3}_.*\.csv$", b)) and classify(b, b"")[1] == "MULTI"
    found = []   # (container path or None, member/file name, bytes)
    for p in iter_year(ydir):
        if p.lower().endswith(".zip"):
            with zipfile.ZipFile(p) as zf:
                for n in zf.namelist():
                    if is_multi_csv(os.path.basename(n)):
                        found.append((p, n, zf.read(n)))
        elif is_multi_csv(os.path.basename(p)):
            found.append((None, p, open(p, "rb").read()))
    ok = set()   # (currency, from, to) whose monthly CSVs reproduce the multi-month rows exactly
    for container, n, data in found:
        b = os.path.basename(n)
        m = re.match(r"statement_(\d+)_([A-Z]{3})_(\d{4}-\d\d-\d\d)_(\d{4}-\d\d-\d\d)\.csv$", b)
        acct, cur, a, z = m.group(1), m.group(2), dt.date.fromisoformat(m.group(3)), dt.date.fromisoformat(m.group(4))
        months, d = [], a.replace(day=1)
        while d <= z:
            last = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)
            if a <= d and last <= z: months.append((d.year, d.month))      # fully covered months only
            d = last + dt.timedelta(days=1)
        rows = wise_rows(data.decode("utf-8", "replace"))
        def ym(r): dd, mm, yy = r["Date"].split("-"); return (int(yy), int(mm))
        inside = collections.Counter((r["TransferWise ID"], r["Amount"]) for r in rows if ym(r) in months)
        outside = [r for r in rows if ym(r) not in months]
        monthly = collections.Counter()
        missing = []
        for (y, mo) in months:
            f = os.path.join(ydir, f"{mo:02d}", f"statement_{acct}_{cur}_{y}-{mo:02d}-01_{y}-{mo:02d}-{(dt.date(y + mo // 12, mo % 12 + 1, 1) - dt.timedelta(days=1)).day:02d}.csv")
            if not os.path.exists(f): missing.append(f"{mo:02d}"); continue
            monthly.update((r["TransferWise ID"], r["Amount"]) for r in wise_rows(open(f).read()))
        same = not missing and inside == monthly
        print(f"{b}: full months {[f'{mo:02d}' for _, mo in months]}, rows {sum(inside.values())} vs monthly {sum(monthly.values())}"
              f"{', monthly CSV missing for ' + ','.join(missing) if missing else ''}{', ' + str(len(outside)) + ' rows outside full months (belong to the next statement)' if outside else ''}"
              f" -> {'SUPERSEDED' if same else 'KEEP'}")
        if same: ok.add((cur, m.group(3), m.group(4)))
    # retire loose Wise files and zips whose EVERY Wise member is superseded; a CSV decides for its PDF twin
    key = lambda b: (lambda r: (r.group(1), r.group(2), r.group(3)) if r else None)(
        re.match(r"statement_\d+_([A-Z]{3})_(\d{4}-\d\d-\d\d)_(\d{4}-\d\d-\d\d)\.(?:pdf|csv)$", b))
    targets = []
    for p in iter_year(ydir):
        b = os.path.basename(p)
        if p.lower().endswith(".zip"):
            with zipfile.ZipFile(p) as zf:
                keys = [key(os.path.basename(n)) for n in zf.namelist() if not n.endswith("/")]
            if keys and all(k is not None and k in ok for k in keys): targets.append(p)
        elif key(b) is not None and key(b) in ok:
            targets.append(p)
    for p in targets:
        print(("TRASH  " if apply else "would trash ") + os.path.relpath(p, ydir))
        if apply: os.remove(p)
    if not targets: print("nothing to retire")
    elif apply: remove_empty_dirs(ydir)

def check(ydir, year, only=None):
    problems = 0; prev = {}
    if only and not os.path.isdir(os.path.join(ydir, only)):
        print(f"{only}/  folder does not exist yet")
        for label in ("bank statement", "Mastercard statements (cards with activity)", "Amex statement PDF", "Amex CSV",
                      "Wise EUR/GBP/USD PDF + CSV", "Stripe balance summary PDF + CSV", "Stripe fees CSV",
                      "Stripe itemised activity CSV (if activity)", "Stripe fee tax invoice (if fees)", "Stripe customer invoices (if any)"):
            print(f"  GAP {label}")
        return 0
    for m in sorted(d for d in os.listdir(ydir) if re.fullmatch(r"\d\d", d)):
        folder = os.path.join(ydir, m); kinds = collections.Counter(); files = sorted(f for f in os.listdir(folder) if not skip_name(f))
        lines = []; bad = 0
        for f in files:
            data = open(os.path.join(folder, f), "rb").read()
            kind, tgt, why = classify(f, data); kinds[kind] += 1
            if tgt not in (None, "MULTI") and tgt != (year, int(m)):
                if tgt[0] == year: lines.append(f"  MISPLACED {f}: {why} (belongs to {tgt[1]:02d}/)"); bad += 1
                else: lines.append(f"  OTHER-YEAR {f}: {why} (belongs to {tgt[0]}-{tgt[1]:02d}, outside this year's folder)")
            if kind in ("unknown", "stripe_receipt"): lines.append(f"  NOTE {f}: {why}")
        for cur, acct in WISE_ACCOUNTS.items():
            base = [f for f in files if f.startswith(f"statement_{acct}_{cur}_{year}-{m}-01_")]
            pdf = [f for f in base if f.endswith(".pdf")]; csvs = [f for f in base if f.endswith(".csv")]
            if not pdf or not csvs: lines.append(f"  GAP Wise {cur}: {'PDF ' if not pdf else ''}{'CSV' if not csvs else ''} missing")
            if csvs:
                rows = wise_rows(open(os.path.join(folder, csvs[0])).read())
                fee_rows = sum(1 for r in rows if r["TransferWise ID"].startswith("FEE-"))
                fees = sum(Decimal(r["Total fees"] or "0") for r in rows if not r["TransferWise ID"].startswith("FEE-"))
                if fees and not fee_rows: lines.append(f"  WISE {cur}: fees folded into amounts: re-download with 'Display transactions with fees shown separately'"); bad += 1
                closing = Decimal(rows[0]["Running Balance"]) if rows else None
                if closing is None and pdf:   # no transactions: the PDF still prints the balance
                    closing = wise_pdf_closing(open(os.path.join(folder, pdf[0]), "rb").read(), cur)
                if closing is None: closing = prev.get(cur)
                opening = (closing - sum(Decimal(r["Amount"]) for r in rows)) if closing is not None else None
                if cur in prev and opening is not None and prev[cur] is not None and opening != prev[cur]:
                    lines.append(f"  WISE {cur}: opening {opening} != previous closing {prev[cur]}"); bad += 1
                if pdf and closing is not None:
                    pc = wise_pdf_closing(open(os.path.join(folder, pdf[0]), "rb").read(), cur)
                    if pc is not None and pc != closing: lines.append(f"  WISE {cur}: PDF closing {pc} != CSV closing {closing}"); bad += 1
                prev[cur] = closing
                if only is None or m == only:
                    lines.append(f"  Wise {cur}: opening {opening if opening is not None else '?'}, closing {closing if closing is not None else '?'} ({len(rows)} rows, {fee_rows} fee lines)")
        for kind, label in (("bank", "bank statement"), ("amex_pdf", "Amex statement PDF"), ("amex_csv", "Amex CSV"),
                            ("stripe_balance_pdf", "Stripe balance summary PDF"), ("stripe_balance_csv", "Stripe balance summary CSV"),
                            ("stripe_fees_csv", "Stripe fees CSV")):
            if not kinds[kind]: lines.append(f"  GAP {label}")
        if only is None or m == only:
            print(f"{m}/  " + ", ".join(f"{k}={v}" for k, v in sorted(kinds.items())))
            for l in lines: print(l)
            problems += bad
    others = [d for d in os.listdir(ydir) if os.path.isdir(os.path.join(ydir, d)) and not re.fullmatch(r"\d\d", d)]
    if others: print(f"NOTE non-month folders: {others}")
    print(f"\n{problems} problem(s)")
    return problems

def tree(ydir, only=None):
    root = os.path.join(ydir, only) if only else ydir
    def walk(p, prefix=""):
        items = sorted(i for i in os.listdir(p) if i != ".DS_Store")
        for i, it in enumerate(items):
            last = i == len(items) - 1
            print(prefix + ("└── " if last else "├── ") + it)
            if os.path.isdir(os.path.join(p, it)): walk(os.path.join(p, it), prefix + ("    " if last else "│   "))
    print(os.path.basename(root)); walk(root)

def place(ydir, year, src, apply):
    pl = Plan(ydir, year)
    for r, _, fs in os.walk(src):
        for f in sorted(fs):
            p = os.path.join(r, f)
            if skip_name(f): continue
            if f.lower().endswith(".zip"):
                with zipfile.ZipFile(p) as zf:
                    for zi in zf.infolist():
                        if not zi.is_dir() and not skip_name(zi.filename): pl.add_file(f"{f} :: {zi.filename}", os.path.basename(zi.filename), zf.read(zi), "zip", p)
            else:
                pl.add_file(os.path.relpath(p, src), f, open(p, "rb").read(), "zip", None)   # 'zip' origin = copy, never move the source
    for op in pl.ops:
        if op[0] == "EXTRACT":
            zpath, name = op[4]
            print(f"{'COPY' if apply else 'would copy'} {op[1]} -> {op[2]}/   [{op[3]}]")
            if apply:
                os.makedirs(os.path.join(ydir, op[2]), exist_ok=True)
                if zpath:
                    with zipfile.ZipFile(zpath) as zf: data = zf.read(op[1].split(' :: ', 1)[1])
                    open(os.path.join(ydir, op[2], name), "wb").write(data)
                else:
                    shutil.copy2(os.path.join(src, op[1]), os.path.join(ydir, op[2], name))
        elif op[0] == "SKIP": print(f"SKIP {op[1]} ({op[3]})")
    for s, why in pl.flags: print(f"FLAG {s}   [{why}]")
    for s, folder, name in pl.conflicts: print(f"CONFLICT {s} -> {folder}/{name} exists with different content (not overwritten)")
    if pl.conflicts and apply: sys.exit(1)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["plan", "apply", "place", "retire-multi", "check", "tree"])
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--month", help="MM, for check and tree")
    ap.add_argument("--root", default=DEFAULT_ROOT, help="the statements folder (default: the accounting shared drive)")
    ap.add_argument("--from", dest="src", help="staging folder for place")
    ap.add_argument("--apply", action="store_true", help="perform the writes (default: dry run)")
    a = ap.parse_args()
    ydir = os.path.join(a.root, str(a.year))
    if not os.path.isdir(ydir): sys.exit(f"no such folder: {ydir}")
    if a.cmd == "plan": print_plan(build_plan(ydir, a.year))
    elif a.cmd == "apply":
        pl = build_plan(ydir, a.year); print_plan(pl)
        if a.apply: execute(pl, ydir)
        else: print("\n(dry run: add --apply to perform)")
    elif a.cmd == "place":
        if not a.src: sys.exit("--from DIR is required")
        place(ydir, a.year, a.src, a.apply)
    elif a.cmd == "retire-multi": retire_multi(ydir, a.year, a.apply)
    elif a.cmd == "check": sys.exit(1 if check(ydir, a.year, a.month) else 0)
    elif a.cmd == "tree": tree(ydir, a.month)

if __name__ == "__main__":
    main()
