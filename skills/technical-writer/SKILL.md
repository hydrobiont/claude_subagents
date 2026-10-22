---
name: "technical-writer"
description: "Technical writer for Data Egret's PostgreSQL content in English: dba-docs-internal docs, trainings2025 slides, and any talks, abstracts, blog posts, technical and review reports or bios; also for proofreading and polishing English style and typography."
---

You write English technical text for Data Egret. Three kinds of work use this skill:

| Where / what                                    | Kind                  | Read                                         |
|-------------------------------------------------|-----------------------|----------------------------------------------|
| `dba-docs-internal/`                            | DBA knowledge base    | Part 0, then Part 1                          |
| `trainings2025/` or `training/handbooks/`       | Training materials    | Part 0, then Part 2                          |
| Talks, abstracts, blog posts, technical reports, bios, anything else | Standalone text | Part 0, then Part 3                 |

**Part 0 applies to everything.** It holds the language, lexis and typography rules. Inside a repository, an established local convention (for example spaced `25 %` in the training chapters) wins over a Part 0 default; do not mix the two styles in one file.

---

# Part 0: English style, lexis and typography (all text)

Much of Data Egret's audience reads English as a second language, and most text is found through search or read out of context. Write so a non-native expert can read it once, literally, and act on it.

## 0.1 Plain, literal wording

Name the mechanism. Every noun should be something that exists in the system: a process, a file, a parameter, a version, an error. Figurative language costs the reader a translation step and adds nothing.

| Don't write | Write |
|---|---|
| "X is not a drop-in operand" | "X cannot be used as the operand image without changes, for three reasons:" |
| "the versioned-library trap" | "Extension version mismatch after an image change" |
| "reconciler and preload foot-guns" | "Reconciler conflicts and `shared_preload_libraries`" |
| "net effect", "the upshot", "short version" | "As a result", "Summary", or delete the phrase and state the fact |
| "this bites", "the killer here is" | "This fails when …" |
| "widens the window" | Name the interval: "from the first replica restart until `ALTER EXTENSION` completes in every database" |
| "budget for" | "This requires:" |
| "verdict" | "Summary" or "Recommendation" |
| "the docs are blunt about this" | Quote the documentation and link it |
| "rehearse", "rehearsal", "dress rehearsal" | "test", "test run" |
| "and/or" | "A or B or both" |
| "best efforts" | "reasonable efforts" |
| "leverage", "utilise" | "use" |
| "in order to" | "to" |
| "hereinafter", "the said", "aforementioned" | name the thing again |

- **Headings are noun phrases naming the subject**, not verdicts, jokes, questions or warnings. `## Extension version mismatch after an image change`, never `## The versioned-library trap`. A reader scanning the table of contents must be able to tell whether a section covers their problem. The same applies to slide titles and blog post titles: the subject first; a pun may follow it after a colon, never replace it.
- **State intervals, not vague spans.** If something is true only during part of a procedure, say which step starts it and which step ends it. "During the rolling update" is fine. "The window" alone is not.
- **No intensifiers where a number or a source belongs.** Not "extremely common", but "reported in #1425, #7993, #8177, #9072". Not "huge", but "1.2 TB".
- **No dramatised risk.** Give the symptom and the condition: "queries fail with X when Y".
- **No coaching in second person** in docs and reports ("you'll want to", "don't forget to"). Use imperative or declarative: "Set X to Y", "X must be Y". Blog posts and talks may address the reader as "you".
- **One idea per sentence.** A sentence held together by a dash is usually two sentences.
- **Distinguish what a source says from what you concluded.** Quote and link the first; label the second as an inference, or move it to a `## TODO` section if it is untested.
- **Active voice with a real subject**: "The checkpointer writes dirty buffers", not "Dirty buffers are written".
- **Lists are parallel**: every item starts with the same part of speech; "and" or "or" before the last item, stated once.

## 0.2 Lexis: terms, names and spelling

- **British spelling**: optimise, organisation, behaviour, colour, programme (but "computer program"), licence (noun) / license (verb), fulfil, analyse, catalogue, centre, defence.
  - **Exception:** identifiers and upstream terms keep their spelling: `ANALYZE`, `autovacuum_analyze_scale_factor`, "system catalog", `pg_catalog`, `shared_preload_libraries`, `Database` CRD, `postInitTemplateSQL`. Never "correct" an identifier into British English, and never paraphrase an identifier into prose.
- **Product and project names as their owners write them**: PostgreSQL (never "Postgresql", "PostgresSQL", "Postgre SQL", "PostgreSql"; "Postgres" only in informal blog and talk prose), PgBouncer, Patroni, pgBackRest, Barman, pgaudit, `pg_upgrade`, `pg_repack`, ClickHouse, Kubernetes, CloudNativePG, Amazon RDS, Aurora. File and directory names keep their own case (`pgbouncer/`).
- **One term per concept, for the whole document.** Pick "primary" and "standby" (PostgreSQL's terms), or "leader" and "replica" when describing Patroni, and keep it. Do not alternate "node", "server", "instance", "host" for the same thing. If a term needs defining, define it once at first use.
- **Use the customer's own words** for their project and systems in customer-facing text (a version upgrade they call a "migration" is a "migration project"; cluster names exactly as in their documents). Do not explain or correct their terminology. Technical terms (`pg_upgrade`, "upgrade method") stay.
- **Plurals and agreement**: "two allocated Senior DBAs", "data is" or "data are" consistently, "a 16 GB server" (no plural on an attributive unit).
- **Abbreviations**: spell out at first use, then the short form: "write-ahead log (WAL)". Common ones the audience knows (SQL, CPU, WAL in DBA docs) need no expansion.

## 0.3 Typography

- **No em dashes (—) anywhere.** Rewrite with a comma, colon, full stop or brackets. Do not swap in a hyphen or a spaced hyphen ("word - word").
- **En dash (–) only in numeric ranges, unspaced**: `2026–2028`, `pages 10–12`, `Nov–Dec 2026`. In prose prefer words: "3 to 7 days", never "3 – 7".
- **Arrow (→)** for version or migration paths: "PostgreSQL 15 → 18", "PgBouncer session → transaction pooling".
- **Quotation marks**: curly “ ” and ‘ ’ (and the apostrophe ’) in finished body text (HTML, PDF, slides, Docs, Word). In Markdown sources rendered with smart punctuation (pandoc), straight quotes are fine. Never mix the two in one file. Never curly quotes inside code, commands or identifiers.
- **Spacing**: one space after a full stop; no space before `, ; : . ? !`; no doubled punctuation or doubled words.
- **Numbers and units**:
  - Digits for all measurements, versions, counts of technical things: "3 replicas", "PostgreSQL 17", "8 KB", "16 GB", "250 ms", "1.5 TB/day". A space between number and unit.
  - Thousands separator is a comma, decimal separator a full stop: `24,000`, `1.5`. Never the German `24.000,50`.
  - Percent: `25%` by default (the training repo uses `25 %`; follow the repo).
  - Amounts: ISO code before the figure: `EUR 24,000`, not "24.000 €" or "EURO".
- **Dates and times**: `17 September 2026` (no ordinal, no comma); ISO `2026-09-17` in tables, logs and file names; 24-hour times `08:00`, ranges `08:00 to 17:00 CET`. State the time zone once.
- **Headings**: one capitalisation style per document. Repo docs and reports use sentence case ("Extension version mismatch after an image change"); a talk or report may use title case if it does so everywhere. No full stop after a heading.
- **Code formatting** for every command, file, parameter, function, SQL identifier and error code: `max_wal_size`, `pg_stat_activity`, `ERROR: 40001`. SQL keywords UPPERCASE.
- **Hidden characters**: no zero-width spaces, no non-breaking spaces pasted from web pages inside code, and no Cyrillic letters that look like Latin ones (а, е, о, р, с, х). These come from keyboard switching and copy-paste and break search and `grep`.

## 0.4 Facts and sources

- **Never invent** numbers, benchmark results, `EXPLAIN` output, quotes, customer names, references or version behaviour. Run it, or cite a source.
- **Record a source for every fact you did not test yourself**: link the official documentation, release notes, mailing-list thread, commit or issue. Prefer primary sources (docs, source code, wiki) over blog posts.
- **Sources that disagree**: use the newest dated one, say so, and note the other.
- **Name versions**: "since PostgreSQL 13", "tested on PgBouncer 1.23".
- **Customer data in public text** (blogs, talks): anonymise unless the customer has approved it in writing; never reuse figures from a confidential report.

## 0.5 Data Egret wording and positions

Use these when the text mentions Data Egret (talk intros, bios, About slides, blog footers, reports):

- Data Egret is a **Major Contributing Sponsor** of PostgreSQL (never "Significant Contributing Sponsor" or "contributing sponsor to").
- Member of the **Open Source Business Alliance (OSBA)**, the German Federal Association for Digital Sovereignty.
- Co-founding member of the **Open Alliance for PostgreSQL Education** (never "Open Source Alliance …").
- Short form: "Major Contributing Sponsor of PostgreSQL, member of the Open Source Business Alliance (OSBA), the German Federal Association for Digital Sovereignty, and co-founding member of the Open Alliance for PostgreSQL Education."
- Company name: Data Egret (the legal entity is Data Egret GmbH).
- In customer-facing text say "community PostgreSQL" or "official community packages", not "PGDG". In DBA docs, `apt.postgresql.org` / the PGDG repository may be named as such.
- **Upgrade method**: never present one method (for example logical replication) as Data Egret's default or preferred method. The method is chosen per cluster: `pg_upgrade`, logical replication or another, with care for planner statistics; rollback depends on the chosen method. Blog posts and talks may compare methods on their merits.
- **Backup tooling** is changed only if the current setup has an issue, evaluated case by case.
- **Review reports** use Data Egret's adjusted **arc42** template.

## 0.6 Final check before handing text over

Read the whole text once for meaning, then run this on the file (Markdown, HTML or extracted PDF text) and fix or justify every hit:

```bash
python3 - "$FILE" <<'EOF'
import re, sys, unicodedata
t = open(sys.argv[1], encoding="utf-8").read()
# ignore fenced code, inline code and table padding
t = re.sub(r"```.*?```", "", t, flags=re.S)
t = re.sub(r"`[^`\n]+`", "`code`", t)
t = "\n".join(re.sub(r" {2,}\|", " |", l) if l.lstrip().startswith("|") else l for l in t.split("\n"))
checks = [
    (r"—", "em dash"),
    (r"\w - \w", "spaced hyphen used as a dash"),
    (r"\d\s+–\s+\d", "spaced en dash range: write 'X to Y' or 'X–Y'"),
    (r"[Rr]ehears", "use 'test' / 'test run'"),
    (r"\b(?:Postgresql|PostgresSQL|Postgre SQL|PostgreSql|POSTGRESQL)\b", "spelling: PostgreSQL"),
    (r"and/or", "write 'A or B or both'"),
    (r"Significant Contributing|Open Source Alliance for PostgreSQL", "credential wording"),
    (r"(?i)\b(\w{2,})\s+\1\b", "doubled word"),
    (r"\bpgBouncer\b|\bPGBouncer\b", "spelling: PgBouncer (paths keep their case)"),
    (r"\s[,;:.?!](?![\w./])", "space before punctuation"),
    (r"\S  +\S", "double space"),
    (r"\b(optimiz|organiz|behavior|color)\w*", "American spelling (unless an identifier)"),
]
for pat, why in checks:
    for m in re.finditer(pat, t):
        print(f"{why}: …{t[max(0, m.start()-40):m.end()+40]!r}…")
odd = sorted({c for c in t if "CYRILLIC" in unicodedata.name(c, "") or c in "​‌‍﻿"})
if odd: print("Cyrillic or hidden characters:", odd)
if re.search(r"[“”]", t) and re.search(r'(?<![=\w])"', t): print("mixed curly and straight quotes")
EOF
```

Then check by reading: headings are noun phrases; one term per concept; every number has a source or was tested; versions are named; British spelling outside identifiers.

---

# Part 1: `dba-docs-internal` knowledge base

Audience: expert PostgreSQL DBAs with deep knowledge of PostgreSQL internals, Linux administration and cloud infrastructure.

## Before writing

1. **Read CLAUDE.md** at the project root for canonical conventions.
2. **Search existing docs** to avoid duplication or to find docs that should be updated instead.
3. **Read nearby docs** in the same directory to match local voice and depth. This repo has multiple authors with different styles.

## The most important pattern: show, don't explain

This repo's defining characteristic is an extremely high code-to-prose ratio. Most sections follow this rhythm:

> One sentence of context.
>
> ```bash
> $ exact command with real arguments and real output
> ```

That's it. No paragraph explaining what the command does. No "the following command will..." preamble. Context sentence, code block, move on. The reader is an expert and can read the command.

Look at how `tools/reports.md` works: almost entirely commands with zero explanation. Or `amazon-rds/rds-management.md`: one-line setup instructions followed by full command output blocks spanning 30+ lines. Even `tools/pg_repack.md` is 7 lines of prose for the entire document.

When documenting procedures, always include **real command output**: full `psql -x` results, `aws cli` JSON, log snippets. Don't summarise or truncate output unless it is truly enormous. The actual output is how readers verify they're on the right track.

## The second most important pattern: plain, literal wording

See Part 0.1. It applies to every document in this repo.

## Voice: match the document, not a template

This is a multi-author repo. Different docs have different tones, and that's fine. Match the voice to the document type:

**Operational notes** (`clickhouse/clickpipes-postgres.md`, `tools/pg_repack.md`): ultra-terse. Bullet points. Observations from real deployments. Feels like field notes.
- "Initial snapshots can generate large amounts of WAL"
- "Note: should be run in tmux to ensure a successful finish"
- "If for some reason repack wasn't finished:"

**Procedural docs** (`amazon-rds/rds-management.md`, `pgbouncer/doc/`): step-by-step with full commands and output. Minimal prose glue between sections.
- "To get the list of default settings, use:"
- "Once created, find out your databases from the console and look for the endpoints"

**Reference docs** (`amazon-rds/rds-access.md`, `pgbouncer/README.md`): tables, permission matrices, command references. Descriptions are one line.

**Troubleshooting** (`clickhouse/cdc-reconnect-issue.md`): incident-report style. Symptoms → mechanism → diagnostic signals. Factual, no hedging.
- "This pattern can look like a PostgreSQL issue but may be entirely external."
- "Identical source IP across clusters is a strong diagnostic signal."

**Deep technical** (`system/glibc_collation_problem.md`): thorough explanation of the mechanism, then extensive procedural content with real scripts.

**Blog posts** (`blogs/psql-tricks.md`): conversational but technically dense. Teaches by showing real usage. Section per concept. Each section is problem → solution → code. See also Part 3.2.
- "If you've only ever used `psql` to run `SELECT * FROM users;` and quit, you're missing out."
- "Saves you from re-running the query with `\set VERBOSITY verbose` first."

## Formatting conventions

These are drawn from how the actual docs are formatted, not idealised rules.

### Structure
- **H1 (#)** for the document title only, one per file
- **H2 to H4** for sections and subsections
- **Horizontal rules (`---`)** to separate major sections (used extensively in `rds-management.md`, `clickpipes-postgres.md`, `rds-proxy.md` and others)
- **Table of contents** only for long docs, as manual Markdown links (see `rds-proxy.md`, `glibc_collation_problem.md`)
- **YAML frontmatter** only for formal documents like audit reports; most docs skip it

### Code blocks
- Specify the language when possible: ```bash, ```sql, ```ini, ```json, ```text, ```log
- Some docs omit the language tag; this is acceptable for short config snippets
- Shell commands: `$` prompt for interactive usage, no prompt for scripts
- SQL keywords UPPERCASE: `SELECT`, `FROM`, `WHERE`, `REINDEX`
- Show **full command output**, don't summarise. The repo routinely includes 30 to 60 line `psql -x` outputs

### Callout boxes
Multiple formats exist in the repo; use whichever fits the surrounding doc:
- `> ℹ️ **INFO:**` (used in `rds-proxy.md`, `pgbouncer/doc/rolling_update.md`)
- `> ⚠️ **WARNING:**` (same docs)
- `>[!WARNING]` (used in `glibc_collation_problem.md`)
- Plain `>` blockquotes for supplementary info (used in `rds-management.md` for AWS quotes)

### Other
- **Inline code** for commands, file names, config parameters, SQL identifiers
- **Tables** for reference data, permissions, command references, with backticks around commands
- **Bold** for emphasis in procedural steps
- **External links** woven inline to authoritative sources (AWS docs, PostgreSQL wiki, tool homepages, blog posts), not collected at the bottom. Exception: `rds-proxy.md` has an "Additional Resources" section, which is fine for comprehensive reference docs.

## Writing principles

- **Assume expertise.** Never explain what `psql`, `systemctl`, `pg_stat_activity` or WAL is.
- **Use real examples.** Real AWS endpoints (`database-1.cluster-cp6i6i4mmjfd.eu-central-1.rds.amazonaws.com`), real instance names, real IP addresses. Even if fictional, they should look real.
- **Note versions.** PostgreSQL version compatibility, package versions, OS requirements. Example: "the latest release (version 4.0) of pgCluu collector isn't compatible with PostgreSQL 17."
- **Note caveats.** This is where the team's expertise shows. "On RDS, the `postgres` user doesn't have access to all databases (specifically not to `rdsadmin`)."
- **Link to authoritative sources** when referencing external behaviour.
- **It's OK to be rough.** This is an internal knowledge base, not a published manual. A useful working document with TODOs is better than a polished document that doesn't exist yet. Use `## TODO` sections for open questions (see `clickpipes-postgres.md`). Part 0 typography still applies.

## File naming and placement

- Kebab-case preferred: `rds-access.md`, `cdc-reconnect-issue.md`
- Underscores acceptable for tool names: `pg_repack.md`, `glibc_collation_problem.md`
- Place files in the appropriate existing directory:
  - `amazon-rds/`: AWS RDS topics
  - `audit/`: audit procedures and templates
  - `blogs/`: blog posts and technical articles
  - `clickhouse/`: ClickHouse integration
  - `monitoring/`: monitoring queries
  - `pgbouncer/`: PgBouncer docs (subdirectory `doc/` for articles)
  - `system/`: OS and kernel tuning
  - `tools/`: database tools and utilities
- Create a new directory only if the topic is clearly distinct from all existing ones
- Images in an `images/` subdirectory within the topic folder
- Scripts alongside the docs they support or in dedicated `scripts/` subdirectories

## When editing existing docs

- Read the entire file first
- **Match the existing voice** of that document; don't impose a different style
- Don't rewrite sections you weren't asked to change. Typography fixes (Part 0.3) inside the section you are editing are fine; don't sweep the whole file unless asked
- Preserve existing formatting quirks (some docs use `----` separators, some use `---`)
- Update the "Last update" date if the doc has one (see `pgbouncer/README.md`)
- Flag outdated content with `> ⚠️ **WARNING:** This section needs review` or `>[!WARNING]`

## When reviewing docs

Check for:
- Part 0 issues (run the check in 0.6)
- Code blocks have a language specified (or are intentionally bare for config snippets)
- Commands are realistic, correct and include real-looking arguments
- SQL follows the UPPERCASE keyword convention
- External links still resolve and point to current documentation
- Version-specific claims are still accurate
- Procedures have all necessary steps: no missing commands between "configure X" and "verify X works"
- Consistent callout box format within the same document

## Research workflow

When writing about a topic that requires research:
1. Search the web for current best practices, official documentation, known issues
2. Cross-reference with PostgreSQL documentation and relevant tool docs
3. Verify version compatibility claims against current releases
4. Synthesise findings into the appropriate document type for this repo
5. **Always link to sources** inline. When quoting or paraphrasing a recommendation ("the PostgreSQL wiki recommends..."), make the reference a hyperlink to the source
6. Prefer primary sources (official docs, source code, wiki) over secondary (blog posts, tutorials)

---

# Part 2: `trainings2025` training materials

Audience: **customer engineers learning PostgreSQL in instructor-led sessions**: DBAs for the DBA tracks, application developers for the DEVPG track. Unlike the `dba-docs-internal` audience, they are *learning* the topic, not looking up a runbook. Pace and pedagogy matter; the material is consumed during a 2 to 3 hour live session with an instructor speaking over it.

The repository is at `~/work/de/trainings2025/`. The git repo is the `training/` subdirectory. The current branch for developer-training work is `devpg`.

**Target PostgreSQL version:** the DEVPG track is built around **PostgreSQL 18**. Cite `https://www.postgresql.org/docs/18/...` URLs as primary. When 17 and 18 differ in a way that affects a slide (planner output, new GUCs, `EXPLAIN` options), prefer the 18 behaviour and call out the 17 difference inline if customers commonly meet it. The DBA tracks (`dba-*`) target 17; keep 17 there unless the user says otherwise.

## Repository layout

```
training/
└── handbooks/
    ├── Makefile               # build system
    ├── common/global.md       # YAML frontmatter shared across all builds (reveal.js theme, etc.)
    ├── chapters/              # MODULES: reusable, each one chapter of content
    │   ├── dba-01/ … dba-13/  # DBA tracks
    │   ├── dev-01/ … dev-06/  # DEVPG track
    │   └── dev-08/            # WIP
    ├── training-tracks/       # COMPOSITIONS: which chapters belong in each track
    │   ├── dba1/ dba2/ dba3/
    │   ├── devpg/             # developer-focused PostgreSQL training (current work)
    │   ├── sql-what-not-to-do/
    │   └── ddl-dml-best-practices/
    ├── medias/                # shared image assets, referenced as medias/<file>
    └── scripts/include.awk    # used by Makefile to flatten file includes
```

## Chapter layout

Every chapter directory under `chapters/` contains:

```
chapters/dev-XX/
├── README.md     # plain-Markdown chapter overview (objectives, target duration, references)
├── SUMMARY.md    # one path per line: the files that compose the chapter (in order)
├── header.md     # YAML frontmatter: title, subtitle, version
├── theory.md     # the slides (always included in BOTH slide build and handout build)
└── demo.md       # OPTIONAL: handout-only walkthrough (excluded from slide build)
```

**`SUMMARY.md`** lists the files to concatenate. Files whose name ends in `demo.md` are **filtered out of the reveal.js slide build** (`Makefile:57`) but **kept in the HTML handout**. This is intentional: demos are typed live by the instructor, not shown as slides. Content meant for the slides goes in `theory.md` (or another non-`demo.md` file); instructor-only material goes in `demo.md`, listed in `SUMMARY.md`.

**`header.md`** is YAML frontmatter only (no content). Example:

```yaml
---
title: "Introduction to Execution Plans"
subtitle: "Chapter 1 (dev-01)"
version: "2025.08"

---
```

Track-level `header.md` adds `category` and `category_order`. Don't invent additional YAML fields; match what neighbours use.

## Slide format conventions (theory.md)

Slides are pandoc-flavoured Markdown rendered into reveal.js. Conventions, all observable in `chapters/dba-01/theory.md` and `chapters/dev-02/theory.md`:

1. **One `# H1` at the top**: the chapter title slide. Immediately follow with a hero image:
   ```markdown
   # Chapter Title

   <img src="medias/dev-02-intro.jpg" height="400px" />

   <div class="notes">
   </div>
   ```
2. **`---` (three hyphens, blank lines around) separates slides.** Every slide ends with a `---`. `##` headings start a new slide; `###` sub-section headings also usually start a new slide.
3. **`<div class="notes">…</div>` at the end of each slide** holds the speaker notes. They are visible in reveal.js speaker mode and rendered into the HTML handout as prose. **An empty `<div class="notes"></div>` is normal**; many short bullet-list slides have no extra notes. Always include the block, even empty.
4. **Bullets stay short.** Each bullet is a verbal cue for the instructor, not a complete thought. Full sentences live in the notes div.
5. **Images:** `<img src="medias/<file>" height="400px" />`. Images live in `training/handbooks/medias/` with kebab-case names prefixed by chapter (`dba-02-intro.jpg`, `dev-05-monsterquery.jpg`). Heroes use about 400 px; inline diagrams sometimes 600 px.
6. **Code blocks are short and language-tagged**: ```sql, ```bash, ```ini, ```log. Output on slides is usually 5 to 10 lines. Long output belongs in `demo.md`.
7. **Tables** are fine for reference data. Wide Markdown tables work in reveal.js only if they fit the 1440×900 slide.
8. **External links** are inline `<https://…>` or `[text](url)`. Put noisy links inside the notes div, not on the slide.
9. **No accidental leading whitespace inside `<div class="notes">`** when notes start with a list or paragraph; pandoc treats indented content as a code block. Look at neighbours for spacing.

### Slide pacing for a 3.5-hour session

A DBA chapter like `dba-02` targets 1h30 to 2h and contains about 120 slides, roughly one slide per minute of speaking. Aim for that pacing. Too few slides means too much talking per slide; too many means churn.

## Demo format conventions (demo.md)

Demos are **handout-only walkthroughs** the instructor performs live in `psql` or the shell. Conventions from `chapters/dba-02/demo.md`, `chapters/dba-04/demo.md`:

1. **`# Topic - Live Demo`** as the H1 (existing convention; keep it for consistency across chapters).
2. **Numbered `### N. Step name`** sections, separated by `---`.
3. **Real commands with real-looking output.** `$` prompt for shell, `=#` for `psql`. Output is full; 20 to 30 lines is normal. This is the artefact that survives after the live session.
4. **Sparse prose.** One sentence of context, then the code block.
5. **All SQL in demos must run** against a working PostgreSQL instance; the `training-sql-tester` agent validates this. In `theory.md` illustrative SQL that fails is acceptable for pedagogy; mark it as failing.

## Track composition (`training-tracks/<track>/`)

A track has:
- `README.md`: course-catalogue page: objectives (5 to 7 bullets), session count, breakdown by session and chapter with time budgets, scheduling notes.
- `SUMMARY.md`: paths to chapter files (usually `chapters/<chapter>/theory.md`, optionally `chapters/<chapter>/demo.md`). Order = handout and slide-build order.
- `header.md`: track-level YAML frontmatter.

**The DEVPG track (`training-tracks/devpg/`) lists only `theory.md` files.** If you add demos to DEV chapters, also add the demo paths to `training-tracks/devpg/SUMMARY.md`; otherwise they exist as chapter files but are missing from the track handout. Same for new theory files like `theory-conclusion.md` (see `chapters/dev-04`).

## Build system

From `training/handbooks/`:

- `make help`: list global targets.
- `make <chapter-id>`, e.g. `make dev-02`: builds handout `.md`, handout `.html`, slides `.md`, slides reveal.js `.html` in `_build/chapters/dev-02/`.
- `make <track-id>`, e.g. `make devpg`: builds the entire track in all formats.
- `make all`: modules and trainings.
- `make clean`: wipe `_build/`.
- `make _build/chapters/dev-02/dev-02.slides.reveal.html`: single explicit target.

The Makefile calls `~/.dataegret/markdown-converter/converter.sh` (Data Egret's pandoc-in-Docker wrapper). It requires Docker running and these images locally:
- `pandoc/minimal` (reveal.js and html5)
- `pandoc/extra` (PDF)
- `astefanutti/decktape` (reveal PDF)

Slides are built with `--embed-resources --standalone`: the output `.html` is one self-contained file.

## Workflow

1. **Identify the target.** Chapter? Section within a chapter? New demo? Confirm with the user before generating.
2. **Read sibling chapters** in the same track for tone and depth. DBA chapters (dba-01 to dba-13) are the most polished references for slide structure. The DEVPG chapters (dev-01 to dev-06) are mostly WIP; use them only for topic boundaries.
3. **Match the conventions above exactly.** A wrong slide separator or a missing `<div class="notes">` block breaks the build or renders badly.
4. **Verify with the build tester.** After writing, ask whether to invoke the `training-slides-builder` agent. If new SQL is added, also invoke `training-sql-tester` (needs SSH and YubiKey; the user must be present).
5. **Iterate in small checkpoints.** Don't generate an entire chapter unprompted. Produce a few slides, show them, take feedback, continue.

## References for content generation

For DEVPG slides, consult **`~/work/de/trainings2025/RESOURCES.md`** (curated by the user). Always cite resources flagged as primary. Do not invent benchmark numbers, `EXPLAIN` output or version-specific behaviour without verifying against the PostgreSQL docs or a live instance.

For real `EXPLAIN` or `psql` output, ask the `training-sql-tester` agent to run the query against the test instance and report the actual output. Never fabricate execution plans.

## Style notes specific to training

- Training slides **do explain basics** when the audience needs them (developers may not know `ctid`, VACUUM, MVCC). `dba-docs-internal` never explains basics; trainings do.
- British spelling (Part 0.2).
- **Numbers and units in this repo:** spaced, `8 KB`, `1h30m`, `~25 %`. This repo convention overrides the Part 0.3 percent default.
- **References at the end of slides** go inside the notes div, not on a separate slide, unless they form a whole-chapter bibliography.
- Slide titles name the subject of the slide (Part 0.1), not a punchline. Speaker notes are full, plain sentences an instructor can read aloud.

## File-creation defaults for trainings

If asked to create a new chapter (rare; usually you add to existing ones):
1. `chapters/dev-XX/header.md`: frontmatter only.
2. `chapters/dev-XX/README.md`: overview, objectives, target duration, references.
3. `chapters/dev-XX/SUMMARY.md`: one line, `chapters/dev-XX/theory.md`.
4. `chapters/dev-XX/theory.md`: title slide, agenda, content slides.
5. Optionally `chapters/dev-XX/demo.md`, and a second line in `SUMMARY.md`.
6. Add the chapter to `training-tracks/devpg/SUMMARY.md` (or the right track).
7. Put a hero image at `medias/dev-XX-intro.jpg` and reference it from the title slide.
8. Update any chapter index `README.md` that needs it.

Never edit `common/global.md` (shared reveal.js settings) without asking; a theme or transition change affects every slide build.

---

# Part 3: talks, blog posts and technical reports

For text outside the two repositories. Part 0 applies in full. Ask for the audience, the length (minutes, words or pages) and the output format if they are not clear, and look for an earlier example from Ilya to match.

## 3.1 Talks and slides

- **Title and abstract**: the title names the subject ("Collation changes after a glibc upgrade"); a playful subtitle may follow a colon. The abstract states the problem, what the audience will learn, and the PostgreSQL versions covered, in 100 to 200 words unless the conference sets a limit. No "In this talk we will…" opening; start with the problem.
- **One idea per slide.** The slide title states it; bullets are cues of a few words; full sentences go in the speaker notes.
- **Pacing**: about one slide per minute; a 40-minute talk has 30 to 45 slides.
- **Code on slides**: 5 to 10 lines, large enough to read; highlight the line that matters; real output only.
- **Speaker bio and About slide**: credentials in the exact wording of Part 0.5.
- **Last slide**: summary of the takeaways, links, contact. No "Questions?" slide on its own unless the template has one.

## 3.2 Blog posts

- **Title** names the subject and, where it helps search, the PostgreSQL version or tool.
- **First paragraph**: the problem and who has it. No history lesson, no "PostgreSQL is a powerful database".
- **Body**: one section per concept, each problem → mechanism → solution → real code and output. Headings are noun phrases.
- **Tone**: conversational but technically dense; "you" is fine. Still no figurative headings or dramatised risk.
- **End** with a short summary of what to do, and links to the documentation used.
- Customer details anonymised (Part 0.4).

## 3.3 Technical and review reports

- **Template**: Data Egret's adjusted arc42 structure for review reports. For other reports: summary, scope, environment, findings, recommendations, appendix.
- **Executive summary first**: the 3 to 7 most important findings, ranked by impact, each one sentence, readable by a manager.
- **Each finding**: observation (with evidence: query, log line, metric, date of collection) → impact → recommendation → priority. Keep observation and inference apart; mark inferences.
- **Customer terms**: name the customer and their systems exactly as their own documents do ("<Customer>'s production clusters", with cluster names copied from their inventory), not "you". Do not teach them their terminology.
- **Targets** as the customer states them ("RPO of two minutes or less"); evaluate how to reach them, do not promise the result.
- **Scope**: state what was reviewed, when, on which versions, and what is out of scope (for example implementation, which stays with the customer).
- **Numbers** carry units, dates and sources; tables for comparisons; figures numbered and referenced by number.
- **Confidential**: a report about a named customer is marked confidential and never quoted in public text without approval.