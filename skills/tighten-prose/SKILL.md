---
name: tighten-prose
description: >-
  Re-read finished prose, cut every word that doesn't earn its place, and replace
  vague or evaluative phrasing with the concrete fact — the word-economy and
  precision self-edit pass. Use when the user asks to tighten, trim, condense,
  or shorten text; cut filler / fluff / padding; make something punchier or more
  concise; remove needless or empty words; make a claim concrete instead of vague
  or poetic; or do a final editing pass before
  shipping a draft (slide, speaker note, abstract, CFP submission, doc, runbook,
  report, commit message, email). Also the canonical discipline the Data Egret
  writing agents apply to their own drafts before returning them. Guards meaning:
  never strips identifiers, version qualifiers, negations, numbers, or
  load-bearing terms — concision serves clarity, never replaces it.
---

# Tighten Prose

A finished draft says everything it needs to. A *good* draft also stops saying
everything it doesn't. This skill is the second part: re-read the text and cut
every word that fails to earn its place.

The rule, in one line: **read it back, weigh each word, and delete any word whose
removal costs no meaning, no precision, and no truth** — and replace any word
that is figurative where a plain technical term exists (see the register test).

This is a *self-edit pass on already-written prose* — run it last, on your own
draft or on text the user hands you. It does not restructure arguments or change
what the text claims; it removes the words that dilute what the text already says.

## The procedure

1. **Finish the draft first.** Don't tighten while composing — you'll censor good
   sentences before they exist. Write it, then switch hats to editor.
2. **Read it back slowly, word by word.** Not paragraph by paragraph. The unit of
   work is the word and the short phrase.
3. **Apply the deletion test to each word:** strike it out and re-read the
   sentence. If the meaning, the precision, and the truth all survive intact, the
   deletion stays. If any of the three is dented, restore the word — it was
   load-bearing.
4. **Prefer the short, plain word and the active verb.** "use" over "utilise",
   "because" over "due to the fact that", "analyse the plan" over "perform an
   analysis of the plan".
5. **Read the result aloud.** If you stumble or run out of breath, the sentence is
   still carrying weight it doesn't need. Cut again.
6. **Stop when every remaining word is doing a job.** Concision is reached, not
   maximised — the goal is "nothing wasted", not "shortest possible".

## What to cut (the usual offenders)

- **Throat-clearing openers:** "This talk will cover…", "In this section we will…",
  "It is important to note that…", "Let me explain…". Open on the content.
- **Empty intensifiers:** *very, really, quite, rather, fairly, somewhat, pretty,
  extremely, actually, basically, simply, just, of course, obviously, clearly.*
  They beg the reader to find the point important instead of making it so.
- **Contentless hedges:** "it could be argued that", "in some sense", "more or
  less", "kind of". (Keep hedges that carry real epistemic content — see below.)
- **Redundant pairs and tautologies:** "each and every", "first and foremost",
  "end result", "future plans", "advance warning", "completely eliminate".
- **Meta-narrative:** "as you can see", "it's worth mentioning", "needless to
  say", "as previously stated". If it's needless to say, don't.
- **Nominalisations that bury a verb:** "make a decision" → "decide", "provide an
  explanation of" → "explain", "is reflective of" → "reflects".
- **Filler connectives:** "in order to" → "to", "due to the fact that" →
  "because", "at this point in time" → "now", "in the event that" → "if".
- **Words the context already supplies:** "the colour blue", "merge together",
  "a total of 12 rows", "PostgreSQL database software".

## The precision test — vague is not concise

The deletion test catches words that say nothing. The opposite failure: a word
that *survives* deletion — cutting it loses meaning — but the meaning it carries
is **vague, evaluative, or poetic** rather than concrete. It passes the deletion
test and still fails technical prose. Don't delete it — **replace it with the
specific mechanism, value, or field name.**

Ask of each claim: *says who, how much, by what mechanism?* If the honest answer
is more specific than the words on the page, write that instead — the vague word
is doing the reader's thinking for them, usually wrongly.

- **Evaluative adjectives with no referent:** "better fidelity", "cleaner", "more
  robust", "powerful", "seamless", "lightweight", "production-grade". Better than
  *what*, measured *how*?
- **Hand-wave verbs:** "handles", "supports", "leverages", "deals with". State
  what it does.
- **Vague quantifiers posing as data:** "fast", "scales well", "minimal
  overhead", "large". Give the number or the bound, or drop the claim.

| Vague (passes deletion, fails precision) | Concrete |
|---|---|
| "PeerDB's default envelope gives better delete fidelity." | "On DELETE, PeerDB's default envelope carries the pre-delete row in `old` (with `REPLICA IDENTITY FULL`); Debezium with schemas off sends `after = null`, so its tombstone row stores empty `content`." |
| "Kompose output needs tweaks to run on Kubernetes." | "Kompose maps the catalog Service to the compose host port 9901, not 5432, so Temporal cannot reach it." |
| "The Kafka engine consumes the topic cleanly." | Delete "cleanly" — it claims nothing the sentence doesn't already say. |

Still a self-edit on finished prose, and it still **never invents facts**: if you
don't know the concrete mechanism or number, that is a `TODO:` flag for the
author, not licence to guess. A vague-but-honest sentence beats a
concrete-but-fabricated one.

## The register test — plain technical words only

A word can pass the deletion test and the precision test and still be wrong
for technical prose because it is **figurative, theatrical, or evaluative**
where a standard technical term exists. Readers experience this as "poetic"
or "AI-written". The rule: **use the term the PostgreSQL, Oracle, or vendor
documentation itself uses; if none exists, use the literal noun or verb.**
Every word and every synonym must survive the question *"define it"* — if the
author would need a metaphor to explain the word, replace the word.

| Figurative / theatrical (seen in real drafts) | Write instead |
|---|---|
| "rehearsal", "dress rehearsal" | "test run", "dry run", "trial load" |
| "head to head" | "in the same test", "under identical conditions" |
| "the winner", "X wins" | "the tool with the better measured result", "X is faster" |
| "weak spot", "Achilles heel" | "limitation" |
| "this buys you X" | "this gives X", "this allows X" |
| "settles the question" | "decides", "answers", "determines" |
| "recipe" | "procedure", "technique", "setting" |
| "story", "journey", "landscape" | "sequence of events", "migration", "set of tools" |
| "cliff", "wall" | "threshold", "limit" |
| "under the hood" | "internally", or name the mechanism |
| "fails loudly / silently" | "returns error X" / "returns success and logs nothing" |
| "in one stroke", "at a stroke" | "at once", "with one change" |
| "the picture", "in hand" | "the result", "available" |
| "sits in", "lives in" | "is in", "is stored in" |
| "boring technology", "battle-tested" | "widely deployed since <year>", or the concrete evidence |

The table is a seed, not a list to memorise: anything a reader could not look
up in a technical glossary is a candidate. This is not the same as the
deliberate-voice exception below — a wry aside the author chose stays; a
metaphor that stands in for a technical term goes.

## What to NEVER cut (load-bearing words)

Concision is in service of clarity and truth. The moment a cut costs either, it
stops being editing and becomes damage. Leave these alone:

- **Technical precision and identifiers:** GUC names (`work_mem`), function and
  catalog names (`pg_class`, `EXPLAIN (ANALYZE, BUFFERS)`), exact feature names
  ("index-only scan", not "index scan"). One wrong noun is worse than ten extra
  ones.
- **Version qualifiers:** "in PostgreSQL 18", "since v16", "before 14". Cutting
  these turns a true statement into a false one.
- **Negations and scope words:** *not, never, only, most, some, all, except,
  unless.* "preserves most statistics" and "preserves statistics" are different
  claims — and the shorter one is wrong.
- **Numbers, units, and conditions:** "8 KB", "~25 %", "when the table exceeds
  shared_buffers". Data is not filler.
- **Deliberate voice:** a wry aside, a direct address to the audience, a
  rhetorical beat the author chose on purpose. Tightening is not flattening.
- **Spelling and house style the deliverable requires** (e.g. British English in
  the training repos: *optimise, behaviour, colour*). Preserve it.

When in doubt between "this word is filler" and "this word is precision", **keep
it and flag it** rather than cutting silently.

## Before / after

| Before | After | What was cut |
|---|---|---|
| "In this section, we will basically take a look at how the planner actually estimates the cost of a sequential scan." | "How the planner estimates sequential-scan cost." | throat-clearing, *basically*, *actually*, dead verb |
| "VACUUM is a very important process that is really quite essential for reclaiming dead tuples." | "VACUUM reclaims dead tuples." | the whole evaluative wrapper |
| "In order to perform an analysis of the query, you should run EXPLAIN ANALYZE." | "Run EXPLAIN ANALYZE to analyse the query." | *in order to*, nominalisation, *you should* |
| "As you can see, the index is used and, first and foremost, the scan is very fast." | "The index is used; the scan is fast." | meta-narrative, redundant pair, *very* |

Counter-example — what a careless pass would wrongly cut:

> "Since PostgreSQL 18, `pg_upgrade` preserves **most** optimizer statistics."

Every word here is load-bearing. Dropping "Since PostgreSQL 18" makes it
version-blind; dropping "most" makes it false (extended statistics aren't
carried over); dropping "optimizer" loses the precision. **Leave it whole.**

## Output

- **Invoked on the user's text:** return the tightened version, then a short
  bulleted list of the notable cuts and register replacements (and any word you kept-and-flagged because
  cutting it would have changed meaning). Don't narrate every deleted "very".
- **Applied to your own draft (the writing agents):** just return the tightened
  draft. The pass is invisible plumbing — the user sees a tighter result, not a
  diff of your editing.
- **If tightening would force a meaning change**, stop and say so instead of
  shipping a shorter-but-wrong sentence. A correct long sentence beats a snappy
  false one every time.
