# The QA round

Run all three passes on every iteration, in this order, on the whole file. Start with
`scripts/report_checks.py REPORT.md`, which lists mechanical findings; fix them, then run the
passes. Delegate the style pass to a fresh `general-purpose` agent when the Agent tool is
available (fresh eyes, no authoring context); otherwise apply the skills yourself. Run every
QA agent on a faster, cheaper model (`model: "sonnet"`; `"haiku"` for mechanical grading);
the coordinating session keeps the default model.

## 1. Technical-writer pass

Three skills, in this order:

1. `tighten-prose`: word economy, the precision test, and the **register test** (plain
   technical words; the table of offenders and replacements is in that skill). The pass drops
   words, never meaning: identifiers, version qualifiers, negations, numbers, units, command
   output and the user's deliberate structure survive.
2. `canonical-tech-names`: product and project names spelled as the projects spell them;
   code blocks, commands and identifiers untouched; mis-cased commands in code flagged only.
3. **Definability check**: every abbreviation expanded at first use and present in the
   Glossary; every domain term defined there with a source; no synonym rotation (one concept,
   one term); every word survives the question "define it". `report_checks.py` lists
   abbreviations that are neither expanded nor defined; the writer closes the list.

British English throughout the body; product names and identifiers unchanged.

## 2. Stakeholder coverage check

Run the `stakeholder-coverage-check` skill on the file. Demand side: Stakeholders, Goals of
improvement, Requirements overview, Issue history. Supply side: Solution strategy items;
Open items count as deferred, never as covered. Report the coverage matrix, the gap fixes and
the orphan recommendations; apply fixes only to text you authored, propose them for text the
user authored.

## 3. Fact check with sources

Rule: external claims (product versions, release dates, tool behaviour, PostgreSQL behaviour,
licence terms, vendor statements) carry a public documentation URL; numbers we measured name
the analysis they come from (the Oracle dump, its export log, the PostgreSQL dump), never an
internal file; anything else is rewritten as an Open item in question form.

Procedure: extract every checkable claim; PostgreSQL behaviour goes to `pg-kb-answerer`
(never answered from memory, per the client workspace rules); other external claims are
verified against the cited page (WebFetch) or by `training-fact-checker` on the file;
measured numbers are checked against the analysis file. Verdicts: CONFIRMED, CONTRADICTED,
OUTDATED, UNVERIFIABLE. Fix CONTRADICTED and OUTDATED in the text; UNVERIFIABLE becomes an
Open item.

## Round report (to the user, in chat)

```
## Placement
<finding → section, one line each; items the user must decide>
## Style pass
<notable cuts, register replacements, tech-name corrections, glossary terms added>
## Coverage
<verdict line of the coverage check; gaps with proposed fixes>
## Fact check
<verdicts; contradicted or outdated items and what changed; unverifiable items now in Open items>
## Open questions for you
<numbered>
```
