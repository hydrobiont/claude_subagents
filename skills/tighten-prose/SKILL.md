---
name: tighten-prose
description: >-
  Re-read finished prose and cut every word that doesn't earn its place — the
  word-economy self-edit pass. Use when the user asks to tighten, trim, condense,
  or shorten text; cut filler / fluff / padding; make something punchier or more
  concise; remove needless or empty words; or do a final editing pass before
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
removal costs no meaning, no precision, and no truth.**

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
  bulleted list of the notable cuts (and any word you kept-and-flagged because
  cutting it would have changed meaning). Don't narrate every deleted "very".
- **Applied to your own draft (the writing agents):** just return the tightened
  draft. The pass is invisible plumbing — the user sees a tighter result, not a
  diff of your editing.
- **If tightening would force a meaning change**, stop and say so instead of
  shipping a shorter-but-wrong sentence. A correct long sentence beats a snappy
  false one every time.
