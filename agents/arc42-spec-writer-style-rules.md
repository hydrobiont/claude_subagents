# arc42-spec-writer — style rules (maintained rubric)

Binding rules for every document this agent produces. The agent proposes
additions after each run; the user approves before anything is added here.
Keep this file a rulebook: one rule per bullet, no essays.

## 1. Document structure (arc42 v8, adapted)

Sections, in order, each with its single question:

1. **Introduction and Goals** — what is being built and for whom; top 3-5
   quality goals; stakeholders and what each needs from this document.
2. **Constraints** — technical, organizational, legal limits the solution
   must obey (given, not chosen).
3. **Context and Scope** — system boundary; external partners; what crosses
   the boundary (business view and technical view).
4. **Solution Strategy** — the few load-bearing decisions, each one sentence
   with a pointer to its ADR in section 9.
5. **Building Block View** — static decomposition: components, their
   responsibilities, their interfaces.
6. **Runtime View** — the scenarios that matter: primary flow, each failure
   or variant flow, one numbered step sequence each.
7. **Deployment View** — environments, hosts, what runs where, what resets
   and when.
8. **Crosscutting Concepts** — rules that apply across components: security,
   idempotency, logging, data protection, naming.
9. **Architecture Decisions** — ADRs (template in §4 below). Every decision
   someone might re-litigate gets one.
10. **Quality Requirements** — measurable quality scenarios; map each to the
    acceptance test that verifies it.
11. **Risks and Technical Debt** — known gaps, accepted risks, open items,
    each with owner and trigger.
12. **Glossary** — every domain term, defined (rules in §3).

**Normative annexes** follow section 12 for contract content arc42 does not
cover: interface/wire contracts, build requirement lists, acceptance test
catalogs, process definitions. Annexes are the binding part other parties
implement and test against; sections 1-11 explain, annexes bind, the glossary
serves both.

## 2. Normative language

- BCP 14 (RFC 2119 + RFC 8174): **MUST, MUST NOT, SHOULD, SHOULD NOT, MAY**,
  capitalized, carry their RFC meaning — and appear **only** in normative
  annexes and explicitly normative subsections. State the BCP 14 conformance
  clause once, in section 1.
- Every SHOULD names the condition under which deviating is acceptable.
- Every MUST is verifiable: reference the acceptance test ID when one exists,
  otherwise tag `Verification: <how>` (manual review is acceptable if stated).
- Non-normative text is marked: `Rationale:` (why), `Note:` (context),
  `History:` (when/who decided, or an ADR reference).
- One normative statement per sentence. Target ≤ 25 words per sentence in
  normative text; split rather than subordinate.
- Name the actor of every verb in normative text. "The e-mail is sent" is
  forbidden; "the module sends the e-mail" is required.

## 3. Terminology

- Every domain term is defined in the glossary. A term is "domain" if a new
  contractor could not define it from general knowledge.
- **One concept, one term.** Pick one and declare aliases once in the
  glossary ("deal — this document's term for the Odoo `crm.lead` record;
  Odoo's UI calls it opportunity"). Never rotate synonyms for variety.
- Expand every abbreviation at first use or define it in the glossary.
- Identifiers (field names, config parameter names, requirement IDs, test
  IDs, stage names, URLs, model names) are exact strings: code-formatted,
  never inflected, never translated, never renumbered.

## 4. ADR template (section 9 entries)

    ### ADR-NNN: <decision as a full sentence>
    - Status: accepted | superseded by ADR-MMM | proposed
    - Date / Deciders: YYYY-MM-DD / <who>
    - Context: <the problem and the forces, 2-4 sentences>
    - Decision: <what was decided, normative phrasing>
    - Alternatives rejected: <each with the one reason it lost>
    - Consequences: <what becomes easier, what becomes harder, follow-ups>

## 5. Precision rules

- Dates ISO 8601. No relative time ("currently", "today", "recently") —
  write "as of YYYY-MM-DD".
- Numbers carry units. Durations name their reference point ("14 d after
  order creation", not "14 days").
- Facts that can drift carry their verification date and source ("verified
  2026-08-14 against `de-booking-bridge.php`").
- A claim without a source is written as `OPEN: <question> — resolved by
  <who/what>`, never as prose that sounds settled.

## 6. Register — banned and required

Banned everywhere in the document: metaphor, idiom, personification,
irony, evaluative adjectives ("clean", "elegant", "robust", "graceful"),
intensifiers ("very", "genuinely", "loudly"), and narrative color.
Replace with the literal mechanism or the measurable fact:

| Banned (seen in real drafts) | Write instead |
|---|---|
| "zombie deals" / "graveyard" | "records left in a non-terminal stage with no pending owner action" |
| "the funnel stays truthful" | "every non-terminal stage implies a defined pending action (REQ/test ref)" |
| "born expired" | "expired at creation time" |
| "fails loudly / silently" | name the mechanism: "raises X / returns 200 and logs nothing" |
| "data rides / lives in / owns" | "is transmitted via / is stored in / is the system of record for" |
| "borrowed rehearsal room" | "shared branch; usage windows are announced; state is deleted after use" |
| "kills the failure mode" | "prevents <failure> by <mechanism>" |
| "reports, not vibes" | "every run produces the report defined in <ref>" |
| "the door" / "the big Pay button" | "the intake endpoint" / "the portal payment control" |
| "teeny moments" / "loose ends" | "unresolved decisions", enumerated with IDs |
| "rehearsal" / "dress rehearsal" | "test run", "dry run" |
| "head to head" / "the winner" | "in the same test" / "the option with the better measured result" |
| "weak spot" / "buys you" / "settles" / "recipe" | "limitation" / "gives" / "decides" / "procedure" |
| "under the hood" / "sits in" / "the picture" | "internally" (or the mechanism) / "is stored in" / "the result" |

Every word must survive the reader's question "define it"; a word that needs a
metaphor to be explained is replaced by the technical term (see the register
test in the `tighten-prose` skill for the running list).

The document may quote a banned phrase only inside a History/Rationale note
when citing an earlier document verbatim, marked as a quotation.

## 7. Layout

- Tables for enumerable facts (environments, parameters, response codes,
  ID catalogs); prose only for what a table cannot carry. Explanations go
  in prose near the table, never inside cells.
- Numbered lists only for ordered sequences; bullets otherwise. Numbering is
  information: if order does not matter, do not number.
- Every diagram or external artifact reference states what the reader gets
  there that this document does not contain.

## 8. Rewrite traceability

- Preserve every requirement, test, and fix ID verbatim (hard rule).
- Ship an old→new section map covering every section of the source.
- Ship a dropped-content list. Empty is the goal; every entry needs an
  individual justification. "Shortened" is not "dropped" — meaning-loss is.
- The document header records: version, status, date, predecessor document
  and its version, and who decided the changes.

## 9. Self-check (run before returning; fix every failure)

1. Does every domain term used appear in the glossary?
2. Does any concept appear under two names without a declared alias?
3. Grep the draft for BCP 14 keywords outside normative sections — zero hits?
4. Grep for "currently|today|recently|soon" — zero hits?
5. Does every MUST have a test ID or a Verification tag?
6. Does every ADR list at least one rejected alternative?
7. Is every actor named (no agentless passive in normative text)?
8. Banned-register scan (§6 table + your own judgment) — zero hits?
9. Is the dropped-content list honest — did you re-read the source end to
   end after writing, checking each normative statement is represented?
10. Did canonical-tech-names and tighten-prose passes run after the last
    content edit?

<!-- proposed additions land below after user approval; newest on top -->
