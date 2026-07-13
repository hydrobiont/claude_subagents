---
name: stakeholder-coverage-check
description: >-
  Verify that every stakeholder expectation, goal of improvement, requirement/user
  story, and reported issue stated in an arc42-based Data Egret report is traceably
  addressed by a concrete item in the Solution strategy. Produces a coverage
  traceability matrix (each expectation → covering solution item(s) → Covered /
  Partial / Gap), a gap list, and orphan recommendations (solution items tied to no
  stated need). Use this skill before delivering or finalizing any workshop, audit,
  discovery, or FinOps report under ~/work/de/clients (real client write-ups AND the
  anonymized_example samples), and whenever the user asks to "check stakeholder
  coverage", "does the solution strategy cover the expectations / goals", "are all
  stakeholders addressed", "traceability check", "coverage matrix", "gap analysis on
  the report", "did we answer what they asked for", or wants to confirm a report's
  recommendations map back to what stakeholders wanted. Reach for it even when the
  user only says "check the report covers everything" — that is this skill.
---

# Stakeholder coverage check

## Why this exists

A consulting report lands only if its **Solution strategy answers what the customer
actually asked for**. It is easy to write a technically excellent set of
recommendations that quietly skips one stakeholder's concern, or to carry a
recommendation that no one asked for while a stated goal goes unaddressed. This skill
is the pre-delivery traceability pass: it forces every stated need to point at a
concrete solution item, and surfaces the mismatches while they are still cheap to fix.

The output is a verification artifact, not an edit. Report what you find; propose
fixes; let the author decide what to change (the author owns the document structure).

## Inputs — the two sides to reconcile

Read the whole report first. Then extract, verbatim or tightly paraphrased:

**Demand side — what the customer wants** (gather from all of these; they overlap but
are not identical, so treat each as a separate source of expectations):

1. **Stakeholders** — each person's stated *expectation* (e.g. "cost reduction",
   "fewer on-call incidents"). A stakeholder listed with no expectation is *not* a
   gap — note them as "no explicit expectation (sponsor/attendee)".
2. **Goals of improvement** — the top quality goals (often ISO 25010).
3. **Requirements overview / user stories** — the "we need to…" statements.
4. **Issue history from the customer** — reported problems are implicit expectations:
   the customer expects each named pain to be resolved.

**Supply side — what the report offers:**

- **Solution strategy** and every subsection (Configuration/infrastructure
  recommendations, Troubleshooting, Observability, or whatever the report uses).
- **Decisions** may also carry commitments.
- **Open items** are *deferred*, not delivered — an expectation covered only by an
  Open item is **Partial (deferred)**, never Covered.

Section names vary across arc42 adaptations ("Recommendations" vs "Solution strategy",
"Goals" vs "Goals of improvement"). Match by intent, not exact heading.

## Procedure

1. **List demand items.** One row per atomic expectation/goal/story/issue. Split
   compound statements ("cost & capacity" → two rows) so each can be judged on its own.
2. **Map to supply.** For each demand row, find the specific Solution-strategy item(s)
   that would actually achieve it. Cite the item by its number/name — a vague topical
   overlap is not coverage.
3. **Classify** each demand row:
   - **✅ Covered** — a concrete solution item, if implemented, achieves it.
   - **🟡 Partial** — touched but incomplete: only part of a compound need is met; the
     fix addresses the symptom not the stated outcome; it depends on an unmeasured
     assumption; or it lives only in Open items/Decisions (deferred).
   - **❌ Gap** — nothing in the report addresses it.
4. **Find orphans.** Solution items that trace to **no** demand row. An orphan is not
   automatically wrong — a good audit surfaces proactive hygiene the customer didn't
   ask about (minor upgrade, backups, kernel tuning). Label each orphan either
   *proactive finding (reasonable)* or *possible scope creep (confirm)*, so the author
   can decide whether to keep it or tie it to a goal.
5. **Flag unverifiable expectations.** A goal too vague to test ("better performance"
   with no metric) can't be confirmed covered — call it out; a measurable target is
   what makes coverage checkable.

Be skeptical, not generous. The entire value of this pass is catching the one need
that slipped through — rubber-stamping everything as Covered defeats the purpose.

## Output format

Always produce these three parts, in order.

### 1. Coverage matrix

| # | Source | Expectation (short) | Covered by (solution item) | Status | Note |
|---|--------|---------------------|----------------------------|--------|------|
| 1 | Goal | order-listing responsive at peak | Now-1 add index | ✅ Covered | 900ms→0.3ms |
| 2 | Story | absorb +40% tenant growth | Now-3, Next-4/7 (headroom) | 🟡 Partial | no explicit capacity projection |
| 3 | Stakeholder (Berger) | cost | — | ❌ Gap | no cost analysis in strategy |

Group rows by source (Stakeholders → Goals → Requirements → Issue history) so it's
obvious each source was checked.

### 2. Gaps and partials — with a fix for each

For every ❌ and 🟡, state what to add or change to close it (a concrete
Solution-strategy item, or an explicit "out of scope" note if that's the honest
answer). This is the actionable part.

### 3. Orphan recommendations

List solution items with no stated need, each labelled *proactive (reasonable)* or
*scope creep (confirm)*.

### Verdict line

End with one line: `Coverage: N/M expectations covered · X partial · Y gaps · Z orphan recommendations`.

## Example (abridged)

**Input:** an on-prem audit whose goals include "nightly reporting finishes before the
business day" and whose Solution strategy raises `work_mem` to stop a reporting query
spilling to disk.

**Output row:**

| # | Source | Expectation | Covered by | Status | Note |
|---|--------|-------------|------------|--------|------|
| 4 | Goal | nightly reporting done before business day | Now-3 raise work_mem | 🟡 Partial | fixes the one identified bottleneck query; total batch runtime not measured, so "before business day" isn't proven |

**Gap fix:** "Measure end-to-end nightly batch runtime before/after; if other queries
dominate, extend the analysis — otherwise upgrade this row to Covered."

## Boundaries

- Verification only. Do not rewrite the report; propose fixes and let the author apply
  them. If asked to close the gaps afterward, that's a separate, explicit step.
- Trace to concrete solution items — never mark Covered on topical resemblance alone.
- Works on real client write-ups and the anonymized examples alike; on samples, the
  content is fictional but the coverage logic is identical.
