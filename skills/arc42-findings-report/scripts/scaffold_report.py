#!/usr/bin/env python3
"""Scaffold a Data Egret arc42 report from the template, or write a comment-free snapshot.

  scaffold_report.py new --customer "Boehringer Ingelheim GmbH" --topic "G104 PAS-X: Oracle to PostgreSQL data migration" \
      --author "Ilya Kosmodemiansky" --out ~/work/de/clients/boehringer_ingelheim_internal/2026/<TICKET>.md [--date 2026-09-17] [--template PATH]
  scaffold_report.py snapshot WORKING.md WORKING-v1.0.md

`new` copies the template, fills title/author/date (long form with weekday), replaces the first H1
with the topic, removes the "delete before use" example lines and appends a Glossary section.
`snapshot` strips every HTML comment block and collapses blank lines. Neither runs git.
"""
import argparse, datetime, os, re, sys

TEMPLATE = os.path.expanduser("~/work/de/clients/arc42_postgres_tmpl/workshop.md")
GLOSSARY = """
---

# Glossary

<!--
Every domain term, abbreviation and product name used in the document, defined once,
alphabetically. Expand abbreviations at first use in the body as well. Give a source
(documentation URL or document) where one exists. One concept, one term: declare aliases here.
Format: **Term** — definition. Source.
-->
"""


def new(a):
    src = open(a.template, encoding="utf-8").read()
    d = datetime.date.fromisoformat(a.date) if a.date else datetime.date.today()
    date_str = f"{d.day:02d} {d.strftime('%B')} {d.year} ({d.strftime('%A')})"
    src = re.sub(r'^title: .*$', f'title: "{a.customer} — {a.topic}"', src, count=1, flags=re.M)
    src = re.sub(r'^author: .*$', f'author: "Data Egret ({a.author})"', src, count=1, flags=re.M)
    src = re.sub(r'^date: .*$', f'date: "{date_str}" # LC_TIME=C date +"%d %B %Y (%A)"', src, count=1, flags=re.M)
    src = re.sub(r'^# PostgreSQL architecture workshop$', f'# {a.h1 or a.topic}', src, count=1, flags=re.M)
    # remove example blocks marked for deletion (blockquote lines following the marker)
    src = re.sub(r'^> Example \(delete before use\):\n(?:>.*\n?)*', '', src, flags=re.M)
    if "# Glossary" not in src:
        src = src.rstrip("\n") + "\n" + GLOSSARY
    if os.path.exists(a.out) and not a.force:
        sys.exit(f"refusing to overwrite {a.out} (use --force)")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(src)
    print(f"scaffolded {a.out} from {a.template}")


def snapshot(a):
    src = open(a.src, encoding="utf-8").read()
    out = re.sub(r'<!--.*?-->\n?', '', src, flags=re.S)
    out = re.sub(r'\n{3,}', '\n\n', out)
    if os.path.exists(a.dst) and not a.force:
        sys.exit(f"refusing to overwrite {a.dst} (use --force)")
    open(a.dst, "w", encoding="utf-8").write(out)
    removed = len(re.findall(r'<!--.*?-->', src, flags=re.S))
    print(f"wrote {a.dst}: {removed} comment blocks removed, {out.count(chr(10))} lines")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new"); n.add_argument("--customer", required=True); n.add_argument("--topic", required=True)
    n.add_argument("--author", required=True); n.add_argument("--out", required=True); n.add_argument("--date")
    n.add_argument("--h1"); n.add_argument("--template", default=TEMPLATE); n.add_argument("--force", action="store_true")
    s = sub.add_parser("snapshot"); s.add_argument("src"); s.add_argument("dst"); s.add_argument("--force", action="store_true")
    a = ap.parse_args()
    (new if a.cmd == "new" else snapshot)(a)


if __name__ == "__main__":
    main()
