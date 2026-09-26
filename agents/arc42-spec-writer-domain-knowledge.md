# arc42-spec-writer — domain knowledge

What this agent has learned across runs: recurring document pathologies,
consumer conventions, confirmed user preferences. Style rules live in
`arc42-spec-writer-style-rules.md`; this file is observations, not rules.

<!-- entries below; newest on top -->

### A scripted sort or filter over a written document deletes everything it does not match (2026-09-21)
Tidying a glossary with a five-line script — slice the table, sort the rows, rejoin — destroyed 500
lines of a finished draft: the slice anchor (`| Acceptance tester | `) also matched an identical
row in the stakeholder table 600 lines earlier, and `"\n".join(rows)` kept only lines beginning
`| `, so every heading and paragraph between the two tables vanished. Two guards follow. Edit a
delivered document only with anchored replace-this-exact-string operations, never with sort,
filter, or any transform whose output is built from a subset of the input; and check the line count
before and after every scripted edit, because a shrink is the only visible symptom. Assume no undo:
this program's `migration/` folder holds the PLAN files but is not a git repository, while the
sibling addons checkout is — so a document there is unrecoverable once overwritten.

### "Must reproduce the current behaviour" is not an acceptance criterion until it names the comparison key (2026-09-21)
The brief for the SLA plan asked that installation leave "the per-ticket set of matched policies
unchanged for all 483 tagged tickets". Worked through, the design archives 12 of the 24 live
policies and creates 16 replacements, so record identity changes by construction while every
ticket's first-response hours stay identical — the test as written fails on a correct
implementation. Whenever a spec promises to reproduce prior behaviour, write which property is
compared (observable outcome, or record identity) and list the properties allowed to change, then
re-derive the expected numbers from the design rather than restating the brief's. Deriving them is
also the cheapest defect finder: the same arithmetic turned "near today's 24 policies" into an
exact 28, and surfaced three customers that gain coverage they did not have.

### Error strings become contract identifiers the moment a consumer matches them (2026-08-18)
A rejection payload's human-readable strings look like prose and get reworded freely — but a
consumer that branches on them has made them identifiers. The booking bridge pins its
"just sold out" message on an exact match of `session_ref: sold out`, and the module's L0 plus
the L1 runner assert all four rejection strings, so a rewording breaks a visitor-facing message
and two suites at once. When a spec defines a machine-readable error list, check who reads it,
then declare the strings immutable in the naming/identifier section — not only in the endpoint's
own requirement, where a later editor rewriting "for clarity" will never look.

### A long-running rewrite outruns the code it describes (2026-08-18)
Between drafting a version and finishing it, the implementation can pass the document: an
"unimplemented work" note became false within hours (the WordPress feed client shipped and
deployed), and a "working tree, uncommitted" provenance line became a released module version.
Before returning, re-grep the draft for implementation-state claims — "uncommitted", "working
tree", "not yet", "until X is implemented", "as of <date>" — and re-verify each against the repo
HEAD, because those are the sentences a reader trusts most and the ones that rot fastest. Prefer
anchoring such claims to a commit hash or a version string over a bare date.

### Runtime-View example lists are unreviewed factual claims (2026-08-17)
A scenario step that enumerates causes — "a WP-Cron retry, a double submission, or a
re-run of a fixture" — reads as illustration and escapes the scrutiny requirements
get, so it drifts from the code without anyone noticing. The booking spec's §6.3
named a double form submission as a delivery carrying an existing idempotency key,
while the bridge mints a fresh UUID v4 per accepted submission, which makes the
second submission a second order. When writing or extending any scenario that turns
on an idempotency key, read the component that *generates* the key before repeating
the document's own cause list; where they disagree, the fix may be either side, so
it is an OPEN item, not a silent correction.

### A new normative annex takes the next number and goes last (2026-08-17)
Consumers cite annex subsections by identifier (`Annex 7 §7.2`), so an additive
annex cannot be inserted where its topic belongs — it takes the next free number
and is appended after the last existing annex, even when that is the provenance
annex and the ordering then reads oddly. Pay for the oddity with one note in the
annex preamble stating why the order is what it is. The alternative, renumbering to
keep topics adjacent, breaks every external citation at once; the ID series per
annex (one prefix per annex, here `POC-`) is what keeps the new material findable.

### Superseding an ADR by editing it destroys the record (2026-08-17)
When a new decision overturns part of an old ADR, the tempting edit is to fix the
old ADR's Context and Decision so the document stops contradicting itself. That
silently rewrites what was decided and when, and the audit question "what did we
believe on 2026-08-13?" becomes unanswerable. The working pattern: leave Context
and Decision verbatim, put the change in the Status line ("accepted; the payment
mechanics are amended by ADR-021"), add a dated `History:` note naming what
changed and what survives, and restate only the Consequences lines that became
false — each with the superseding ADR and its date. Consequences are the one part
a cold reader will act on, so a false one cannot be left standing behind a note.

### The retirement unit is usually a clause, not an identifier (2026-08-17)
A rewrite brief that says "retire IDs explicitly where the requirement does not
survive" can produce an empty retirement list and still lose content: in practice
a re-decision leaves the identifier intact and kills one clause inside it — a
manifest dependency, a cron name, a step-0 assertion, "with the income account
per finance guidance". Diff the requirement bodies mechanically (split the annexes
on `**ID**`, compare normalized text) and ship a clause-replacement table in the
provenance annex: identifier, clause replaced. Without it, the old→new map says
"amended" and no reader can tell what left the contract.

### Test runners carry sub-IDs the spec never declared (2026-08-15)
The booking spec's catalog defines BOOK-01…BOOK-10, but
`tests/booking/run-book-suite.sh` emits BOOK-01b, BOOK-04a and BOOK-04b as
separate verdict rows. Those identifiers are consumer-visible — they appear in
committed reports — yet exist only in the runner. Before rewriting any
acceptance catalog, read the runner and CI scripts as well as the spec, and
record the sub-IDs as notes under their parent test; a rewrite that lists only
the spec's IDs silently orphans the ones the reports actually cite.

### Removed config items survive in procedural checklists (2026-08-15)
v1.1 removed `return_base_url` in §A2 and §B6, but §D2.3's parenthetical list of
re-arm steps still said "return URLs" — a contradiction inside one document,
invisible because the two statements are 250 lines apart and only one names the
parameter. Pathology: a decision to drop a configuration item lands in the
definition sections and misses the checklists that enumerate the same items in
prose. When a source records a removal, grep the removed identifier *and* its
plain-language paraphrase across the whole document before assuming the removal
is complete.

### Data Egret spec consumers reference one file by path (2026-08-15)
The booking-integration program's agents (`odoo-acceptance-tester`, the WP
bridge session, the L1 runner docs) all reference
`specs/booking-integration-spec.md` as a single path, and test/fix IDs
(BOOK-xx, WPB-xx, PAY-xx, WPB-fix-x) appear in code comments and reports.
Rewrites in this org must stay single-file and ID-stable unless every
consumer is updated in the same change.

### The user's documented style complaint (2026-08-15)
The user rejected figurative register in specs explicitly: "poetry and
wording where you can't define every word and explain why you use it."
Confirmed direction: arc42 structure, defined terms, stated rationale.
This is the agent's founding mandate; treat register violations as defects,
not taste.
