---
name: arc42-findings-report
description: >-
  Turn analysis findings, call notes and research (dump analyses, measurements, tool
  comparisons, migration plans, risks) into a customer report in Data Egret's arc42-based
  PostgreSQL template (~/work/de/clients/arc42_postgres_tmpl/workshop.md), and run the
  standing QA round on every iteration: technical-writer pass (tighten-prose with the
  register test, canonical-tech-names, glossary and definability check), stakeholder
  coverage check, and fact check with sources. Use whenever the user says "put this into
  the arc42 template", "arc42 report", "IRC 42" or "arc 42" (speech-to-text for arc42),
  "workshop report", "discovery report", "PoC report", "client report from these findings",
  "move the findings into Solution strategy / Open items", or, after reshaping a report,
  "run the QA round again" or "check the report". Reach for it even when the user only says
  "make a report out of this" for a Data Egret customer engagement.
---

# arc42 findings report

Purpose: produce and iterate a customer-facing report in the Data Egret arc42 template from
whatever findings exist, so that the customer reads facts, variants and open questions in
the structure they know, in plain technical English, with every term defined. The user owns
the document structure: the skill proposes placements and asks; it never reorganises the
user's edits.

Read `references/section-mapping.md` before placing anything, `references/qa-round.md`
before every QA round, and `references/files-and-frontmatter.md` before creating or
snapshotting a file.

## Inputs

Any findings material: an existing write-up (for example a migration analysis report), an
analysis folder with tables and JSON, notes from calls, and the conversation itself. Start
by listing what you have: one line per finding with its source file or conversation point.

## Workflow

1. **Inventory and mapping proposal.** Map every finding to a template section using the
   rules in `references/section-mapping.md`. Then ask the user, in one message, about
   (a) findings you cannot place with confidence, (b) information the template needs and
   the material lacks (stakeholders and their expectations, goals of improvement, access
   and communication, timeline), (c) the target file: Odoo ticket ID or a meaningful name.
   Do not draft before the user has answered; the placement decisions are theirs.
2. **Scaffold** the file from the template with `scripts/scaffold_report.py` (frontmatter,
   title, Glossary section appended). The template's HTML guidance comments stay in the
   working file as checklists.
3. **Draft** section by section. Observations from the system and statements heard from
   the customer go to Introduction and goals (Current architecture and setup, Issue history,
   Requirements overview as user stories); variants and comparisons go to Solution strategy
   with the per-item fields the template asks for; unresolved questions go to Open items;
   Decisions holds only what the customer agreed; risks and debts with impact, likelihood,
   priority, mitigation and owner. Detail stays inline: full tables live in the section
   they support, no appendices. Every external claim carries a source link; every measured
   number cites the analysis file it comes from. British English.
4. **Glossary.** Every domain term, abbreviation and product name is defined once in the
   Glossary section, alphabetically, with a source where one exists; abbreviations are also
   expanded at first use in the body. One concept, one term: declare aliases in the
   glossary, never rotate synonyms.
5. **QA round** (`references/qa-round.md`), in this order: technical-writer pass,
   stakeholder coverage check, fact check. Run `scripts/report_checks.py` first; it lists
   register offenders, undefined abbreviations, relative-time words, American spellings,
   template placeholders and structure problems, so the passes start from a clean list.
6. **Round report** to the user: what was placed where, the QA results (cuts and
   replacements, coverage matrix verdict line, fact-check verdicts), the open questions
   that remain, and the terms added to the glossary. Keep it short; the report is the
   deliverable, the round report is the log.
7. **Next round.** When the user reshapes the document, rerun steps 4 to 6 on the whole
   file. Refine the user's text; never revert structure, tone or claims the user
   introduced. Factual problems in user-authored text are flagged, not overwritten.
8. **Snapshot** only when the user declares a version: `scripts/scaffold_report.py snapshot
   IN OUT` writes `<name>-vX.Y.md` without template comments; add the link line to the
   client Readme. Compilation to HTML and PDF is a separate request to `client-report-builder`.

## Rules that do not bend

- Never run git commands in a client repository; the user commits.
- Never invent stakeholders, expectations, goals, access details or decisions; ask.
- Never put a recommendation into Decisions; recommendations and variants belong to
  Solution strategy until the customer agrees.
- Never leave a claim unsourced: an unsourced statement becomes an Open item written as a
  question.
- Plain technical register: the term the PostgreSQL, Oracle or vendor documentation uses;
  no figurative or theatrical vocabulary ("test run", not "rehearsal"); every word must be
  definable if the user asks. The register table is in the `tighten-prose` skill.
- No relative time ("currently", "recently"): write the date.
- Internal matter stays out of the customer document: agent names, our tooling, hourly
  figures, file names or paths of any kind. The report is one self-contained document: a
  number is sourced by naming the analysis it comes from ("analysis of the Oracle dump",
  "analysis of the Oracle export log", "analysis of the PostgreSQL dump", "workshop of
  <date>"), never by an internal file or a Data Egret document.
- Facts about the customer's environment that come from an earlier engagement (for example
  the target platform described in a workshop) and are not confirmed for the scope at hand are
  not stated in the introduction or constraints as facts; they become an Open item that names
  the alternatives without arguing for one, and the text that depends on them is written
  conditionally.
