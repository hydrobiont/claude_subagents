#!/usr/bin/env python3
"""Mechanical checks on an arc42 findings report before the QA passes.

  report_checks.py REPORT.md [--template PATH] [--snapshot]

Reports: frontmatter fields, template placeholders left in, top-level section order against
the template, Glossary presence, abbreviations neither expanded at first use nor defined in the
Glossary, register offenders (figurative or theatrical words), relative-time words, American
spellings, markdown links without http, comment blocks (must be zero with --snapshot).
Code blocks, inline code and HTML comments are excluded from the text checks. Exit code 1 when
any check fails; warnings do not change the exit code.
"""
import argparse, os, re, sys

TEMPLATE = os.path.expanduser("~/work/de/clients/arc42_postgres_tmpl/workshop.md")
REGISTER = {
    r"\brehears(al|als|ed|e)\b": "test run / dry run", r"\bhead[- ]to[- ]head\b": "in the same test",
    r"\bwinner\b": "the option with the better measured result", r"\bweak (spot|point)\b": "limitation",
    r"\bbuys?\b (you|us|time|concurrency)": "gives", r"\bsettle[sd]?\b (the|this|it|which|whether)": "decides / determines",
    r"\brecipes?\b": "procedure / technique", r"\bjourney\b": "migration / process", r"\blandscape\b": "set of systems / tools",
    r"\bcliff\b": "threshold", r"\bunder the hood\b": "internally", r"\b(fails|failing) (loudly|silently)\b": "returns error X / logs nothing",
    r"\bin one stroke\b": "at once", r"\bsits in\b": "is in", r"\blives in\b": "is stored in", r"\bbattle[- ]tested\b": "deployed since <year>",
    r"\bboring technology\b": "widely deployed", r"\bseamless(ly)?\b": "without manual steps", r"\brobust\b": "state the property",
    r"\belegant\b": "delete", r"\bpowerful\b": "state the capability", r"\bleverag(e|es|ed|ing)\b": "use",
    r"\b(very|really|quite|basically|simply|obviously|clearly)\b": "delete", r"\bstory\b": "sequence of events",
    r"\bthe picture\b": "the result", r"\bin hand\b": "available", r"\bpays? off\b": "is worth the cost", r"\bbet\b": "assumption",
}
RELATIVE_TIME = r"\b(currently|recently|nowadays|at the moment|these days|today|lately|soon)\b"
AMERICAN = {"organization": "organisation", "organizations": "organisations", "optimize": "optimise", "optimized": "optimised",
            "optimizes": "optimises", "optimizing": "optimising", "optimization": "optimisation", "analyze": "analyse", "analyzed": "analysed",
            "analyzing": "analysing", "behavior": "behaviour", "behaviors": "behaviours", "color": "colour", "center": "centre",
            "centers": "centres", "catalog": "catalogue", "license": "licence (noun)", "favor": "favour", "favors": "favours", "modeling": "modelling",
            "labeled": "labelled", "canceled": "cancelled", "prioritize": "prioritise", "prioritized": "prioritised", "recognize": "recognise",
            "summarize": "summarise", "customize": "customise", "customized": "customised", "utilize": "use"}
SQL_WORDS = {"SELECT", "INSERT", "UPDATE", "DELETE", "MERGE", "CREATE", "ALTER", "DROP", "TRUNCATE", "COPY", "FREEZE", "VACUUM", "ANALYZE", "ANALYSE",
             "REFRESH", "MATERIALIZED", "VIEW", "INDEX", "TABLE", "SCHEMA", "SEQUENCE", "CONSTRAINT", "FOREIGN", "KEY", "PRIMARY", "UNIQUE", "CHECK",
             "NOT", "NULL", "DEFAULT", "WITH", "WITHOUT", "TIME", "ZONE", "LOCAL", "DATE", "TIMESTAMP", "INTERVAL", "CHAR", "VARCHAR", "NCHAR", "TEXT",
             "RAW", "LONG", "CLOB", "BLOB", "NCLOB", "BFILE", "NUMBER", "FLOAT", "INTEGER", "BIGINT", "SMALLINT", "NUMERIC", "BOOLEAN", "BYTEA", "XMLTYPE",
             "ROWID", "UROWID", "FLASHBACK", "SCN", "UNLOGGED", "LOGGED", "BEGIN", "COMMIT", "ROLLBACK", "SET", "RESET", "SHOW", "EXPLAIN", "GRANT",
             "REVOKE", "ORDER", "GROUP", "WHERE", "FROM", "JOIN", "UNION", "EXCEPT", "VALIDATE", "VALID", "CASCADE", "RESTRICT", "DEFERRABLE", "STDIN",
             "STDOUT", "CSV", "FULL", "PARALLEL", "TYPE", "OWNER", "ACL", "COMMENT", "TRIGGER", "FUNCTION", "PROCEDURE", "PACKAGE", "SYNONYM", "DIRECTORY",
             "DATABASE", "LINK", "ROLE", "USER", "PROFILE", "SYS", "SYSTEM", "PUBLIC", "TOC", "OID", "LSN", "WAL", "XID", "MVCC"}
GENERAL_ABBR = {"GB", "MB", "KB", "TB", "PB", "CPU", "RAM", "SQL", "URL", "HTTP", "HTTPS", "ID", "IDS", "IT", "PDF", "HTML", "CSV", "JSON", "XML",
                "UTC", "GMT", "CEST", "CET", "ISO", "OS", "IP", "DNS", "SSH", "TLS", "SSL", "API", "REST", "USB", "I", "A", "H", "M", "L", "P1", "P2", "P3",
                "S", "NN", "OK", "AM", "PM", "EU", "US", "UK", "DE", "GMBH", "AG", "SE", "EE", "TOC"}


def strip_code_and_comments(text):
    text = re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    text = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", "", text)
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report"); ap.add_argument("--template", default=TEMPLATE); ap.add_argument("--snapshot", action="store_true")
    ap.add_argument("--allow", default="", help="comma-separated identifiers to ignore in the abbreviation check (schema names, product codes)")
    a = ap.parse_args()
    allow = {x.strip().upper() for x in a.allow.split(",") if x.strip()}
    raw = open(a.report, encoding="utf-8").read(); lines = raw.split("\n")
    fails, warns = [], []
    # frontmatter
    if not raw.startswith("---\n"): fails.append("frontmatter: file does not start with ---")
    head = "\n".join(lines[:20])
    for key in ("title:", "author:", "date:"):
        if not re.search(rf"^{key}\s*\S", head, re.M): fails.append(f"frontmatter: {key} missing")
    if not re.search(r'^author: "?Data Egret \(', head, re.M): fails.append("frontmatter: author must start with 'Data Egret ('")
    if not re.search(r"^(\.\.\.|---)$", "\n".join(lines[1:20]), re.M): fails.append("frontmatter: not closed with ... or --- within 20 lines")
    # placeholders
    body_nocomment = strip_code_and_comments(raw)
    for pat, label in ((r"<Customer Name>", "template title placeholder"), (r"\(\.\.\.\)", "author placeholder"), (r"delete before use", "example block"),
                       (r"<[A-Za-z][A-Za-z /+-]{2,40}>", "angle-bracket placeholder")):
        for i, ln in enumerate(body_nocomment.split("\n"), 1):
            if re.search(pat, ln): fails.append(f"placeholder ({label}) line {i}: {ln.strip()[:80]}")
    # section order
    tmpl_h1 = [m.strip() for m in re.findall(r"^# (.+)$", open(a.template, encoding="utf-8").read(), re.M)][1:]  # skip document H1
    doc_h1 = [m.strip() for m in re.findall(r"^# (.+)$", raw, re.M)]
    missing = [h for h in tmpl_h1 if h not in doc_h1]
    if missing: fails.append(f"sections missing: {missing}")
    order = [h for h in doc_h1 if h in tmpl_h1]
    if order != [h for h in tmpl_h1 if h in doc_h1]: fails.append(f"section order differs from template: {order}")
    if "Glossary" not in doc_h1: fails.append("Glossary section missing")
    # glossary terms
    gl_terms = set()
    if "Glossary" in doc_h1:
        gl = raw[raw.index("# Glossary"):]
        gl_terms = {m.lower() for m in re.findall(r"^\s*(?:[-*]\s*)?\*\*([^*]+)\*\*", gl, re.M)}
        gl_terms |= {m.lower() for m in re.findall(r"^\|\s*\*?\*?([^|*]+?)\*?\*?\s*\|", gl, re.M)}
    body = body_nocomment
    if "# Glossary" in body: body = body[:body.index("# Glossary")]
    abbrs = {}
    for i, ln in enumerate(body.split("\n"), 1):
        for m in re.finditer(r"(?<![\w/.-])([A-Z][A-Z0-9]{1,}(?:/[A-Z0-9]+)?)(?![\w.-])", ln):
            t = m.group(1)
            if t in GENERAL_ABBR or t in SQL_WORDS or t in allow or t.upper() in gl_terms or re.fullmatch(r"[A-Z]?\d+", t) or len(t) > 12: continue
            if re.search(r"\d", t) and not re.fullmatch(r"[A-Z]{1,4}\d", t): continue  # identifiers with digits: PDA23P1, AL32UTF8, VARCHAR2
            if t.endswith("SYS") or t.endswith("USER"): continue  # Oracle schema naming
            abbrs.setdefault(t, i)
    undefined = []
    for t, first in abbrs.items():
        expanded = re.search(rf"[A-Za-z][A-Za-z -]+\s\({re.escape(t)}\)", body) or re.search(rf"\b{re.escape(t)}\s\([A-Za-z][^)]{{3,}}\)", body)
        if not expanded and t.lower() not in gl_terms: undefined.append(f"{t} (first line {first})")
    if undefined: warns.append("abbreviations neither expanded at first use nor in Glossary: " + ", ".join(sorted(undefined)))
    # register, relative time, spelling, links
    for i, ln in enumerate(body_nocomment.split("\n"), 1):
        low = ln.lower()
        for pat, rep in REGISTER.items():
            if re.search(pat, low): warns.append(f"register line {i}: /{pat}/ -> {rep}: {ln.strip()[:90]}")
        if re.search(RELATIVE_TIME, low): warns.append(f"relative time line {i}: {ln.strip()[:90]}")
        for us, gb in AMERICAN.items():
            if re.search(rf"\b{us}\b", ln) or re.search(rf"\b{us.capitalize()}\b", ln): warns.append(f"spelling line {i}: {us} -> {gb}")
        if re.search(r"\]\((?!https?://|#|mailto:)[^)]+\)", ln): warns.append(f"link without http line {i}: {ln.strip()[:90]}")
    comments = len(re.findall(r"<!--.*?-->", raw, flags=re.S))
    if a.snapshot and comments: fails.append(f"snapshot contains {comments} comment blocks")
    print(f"# report_checks: {os.path.basename(a.report)}\n")
    print(f"- lines: {len(lines)}, words: {len(raw.split())}, comment blocks: {comments}, H1 sections: {len(doc_h1)}")
    print(f"- FAIL: {len(fails)}  WARN: {len(warns)}\n")
    for f in fails: print(f"FAIL {f}")
    for w in warns: print(f"WARN {w}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
