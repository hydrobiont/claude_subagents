# Conference Abstract Writer — Domain knowledge & style corpus

Persistent notes for the `conference-abstract-writer` agent. This file is **seeded** (not empty): it carries the distilled house style plus a corpus of Ilya Kosmodemiansky's real, accepted PostgreSQL conference abstracts so the agent can few-shot against the genuine voice every run.

The agent reads this file at the start of every invocation, and appends durable learnings (confirmed phrasings the user liked, new accepted abstracts, recurring corrections, event-specific length limits) under the marker at the bottom.

---

## The house voice — Ilya Kosmodemiansky

Author profile: CEO & co-founder of Data Egret, PostgreSQL consultant/architect/DBA. Main focus: database **performance and optimization**, Linux internals, operational reality. Audience at his talks: DBAs, DevOps, and engineers — practitioners, not academics. Non-native English speaker, but the published abstracts read clean and direct; the agent produces grammatically clean English while keeping the directness.

### The "Kosmodemiansky arc" (the structural signature)

Most of his abstracts follow this five-beat flow as a single flowing paragraph:

1. **Hook** — an aphoristic, present-tense statement that the problem is *eternal and everyday*. Establishes universal relatability before any specifics. ("Input-output performance problems are on every day agenda for DBAs since the databases exist." / "'best practices' are plain boring and often are being ignored.")
2. **Baseline + its limit** — acknowledge the easy, known answer (a checklist, best practices, the obvious tool), then pivot: it's not enough / it's boring / you hit corner cases / you really need to understand *why*.
3. **Promise of mechanism over recipe** — state that the talk explains how the thing *actually works* underneath, using concrete machinery nouns. ("how database pages travel from disk level to database own shared memory and back.")
4. **The itinerary** — one breathless, comma-separated sentence enumerating the concrete subtopics. ("We will discuss memory structures, swap and page-out daemons, filesystems, schedulers and IO methods.")
5. **Comparative / accessibility close** — a cross-engine comparison (PostgreSQL vs Oracle vs MySQL), a practical payoff, or a note that the talk is broadly accessible. ("anyone could come and take something useful away.")

Not every abstract hits all five, and the order can flex — but beats 1, 3 and 4 are almost always present. The hook is the most important and most distinctive beat.

### Voice rules

- **First person, field authority.** Grounded in real consulting experience: "over the years of working with Postgres, my colleagues and I have collected…". He has *seen* these problems in production.
- **Direct address to the audience.** "you need to get your data fast", "I will explain you why such practices are bad".
- **Confident and a little wry.** Playful framings land well (worst-practices > best-practices; "reshuffle the deck to draw ten random slides"; "plain boring").
- **Flowing prose, never bullets.** The bullets are the *input* to this agent, not the output. The abstract is 1 paragraph (occasionally 2), roughly **80–150 words**.
- **Practical, operational framing.** "everyday agenda", "corner-cases", real DBA pain. Mechanism in service of operations, not theory for its own sake.
- **Concrete nouns over adjectives.** He names the actual machinery (page-out daemons, schedulers, shared buffers, WAL) rather than stacking superlatives.

### Anti-style (avoid)

- Bullet lists or section headers inside the abstract.
- Marketing fluff and stacked superlatives ("revolutionary, game-changing, cutting-edge").
- Academic-paper register ("In this paper we present…", "We propose a novel…").
- Over-hedging ("might possibly perhaps help in some cases").
- Burying the hook — never open with "This talk will cover…". Open with the *problem*.

### Titles

His titles are plain, specific, and often carry a scope/time marker or a twist:
- "Linux IO internals for PostgreSQL administrators in 2023" (the *"in 20XX"* marker signals a refreshed, current take).
- "PostgreSQL worst practices" (the inversion twist).
- "An ultimate guide to upgrading your PostgreSQL installation".
- "Practical transactions theory for PostgreSQL users" ("Practical … for … users" framing).
- "PostgreSQL on Linux, up and running".

When proposing title variants, prefer: a concrete subject + audience + optional year/scope marker, or a memorable inversion. Avoid clickbait and colons-stacked-on-colons.

---

## Corpus — real accepted abstracts (few-shot reference)

**Linux IO internals for PostgreSQL administrators in 2023** (PGConf.EU 2023; also run 2024, and earlier "…in 2020", SCALE):
> Input-output performance problems are on every day agenda for DBAs since the databases exist. Volume of data grows rapidly and you need to get your data fast from the disk and moreover - fast to the disk. For most databases there is a more or less easy to find checklist of recommended Linux settings to maximize IO throughput. In most cases that checklist is good enough. But it is always better to understand how it works, especially if you run into some corner-cases. This talk is about how IO in Linux works, how database pages travel from disk level to database own shared memory and back and what kind of mechanisms exist to control this. We will discuss memory structures, swap and page-out daemons, filesystems, schedulers and IO methods. Some fundamental differences in IO approaches between PostgreSQL, Oracle and MySQL will be covered.

*(Annotated: beat 1 = "on every day agenda … since the databases exist"; beat 2 = "checklist is good enough … but it is always better to understand"; beat 3 = "how database pages travel from disk … and back"; beat 4 = "memory structures, swap and page-out daemons, filesystems, schedulers and IO methods"; beat 5 = the Oracle/MySQL comparison.)*

**PostgreSQL worst practices** (PGConf.EU 2018 / PGConf.US 2017 / SCALE):
> This talk is prepared as a bunch of slides, where each slide describes a really bad way people can screw up their PostgreSQL database and provides a weight - how frequently I saw that kind of problem. Right before the talk I will reshuffle the deck to draw ten random slides and explain you why such practices are bad and how to avoid running into them.

His framing of it: *"'best practices' are plain boring and often are being ignored… worst practices are way more exciting and, more importantly, we learn much more through our mistakes."* And: *"maybe one of the most open talks at the conference — anyone could come and take something useful away."*

**Themes he returns to:** IO / Linux internals, performance & optimization, autovacuum/VACUUM ("Autovacuum, explained for engineers"), major-version upgrades, configuration, transactions theory ("Practical transactions theory for PostgreSQL users"), PostgreSQL-on-Linux operations, and more recently Change Data Capture (CDC) / PostgreSQL as a real-time analytics source (PGConf.DE 2026).

**How expensive is your query? A practical guide to optimizing Postgres with the budget in mind** (drafted with this agent + manually finalised by Ilya, 2026-06 — the best calibration sample for the *current* precise/technical long-form voice; note the 3-paragraph layout, "your Postgres", DevOps in the audience line, and the plainly-stated savings range):
> When a Postgres workload starts costing too much, the usual reaction is to add hardware — a bigger instance in the cloud, or more cores, memory and faster disks on-premise. That is almost always the expensive answer, and almost always the wrong place to start. FinOps grew up as a cloud practice, but cost-per-query thinking applies to Postgres almost identically whether it runs in the cloud or on your own servers: the cost is driven by the workload, so the workload is what you optimize first.
>
> In FinOps practice the database is one of the largest and most common cost line-items to attack, precisely because databases are expensive — especially when they are not operated properly. Over the years my colleagues and I have seen the same cost-explosion drivers again and again — too many connections, lock contention, and unnecessary IO — and the same excuse for ignoring them: optimizing every query by hand costs more DBA hours than anyone wants to pay. This talk answers where to start instead. I will show how to set up workload analysis with pg_stat_statements and Postgres log analysis, and how to turn that into a repeatable routine that keeps queries performing well and heads off cost spikes. There is a real obstacle here: DBA and consultant time is itself expensive, so teams avoid optimization because their own engineering time costs money too, and the problem compounds. The answer is to make optimization a routine rather than a one-off heroic effort — it takes a modest amount of time, but done regularly it keeps databases performing well as they change.
>
> That is one of the key takeaways: I will show how to determine where most of the cost actually sits, how to approach that as a performance audit, and how to make that audit a regular, repeating routine as your Postgres and its workload keep changing. Within that routine, we will look at concrete cases: assigning each microservice on a shared database a cost budget and querying what share of the total workload its connections actually consume — which often reveals that much of the load comes from services that are not the most valuable to the business; and the 'I want analytics on everything' pattern, where keeping all data in the operational database for analytics leaves it bloated and oversized, when aggregation, proper retention and routing analytics to the right data platform is far cheaper. I will also show how to decide — and defend to managers and teammates — when more hardware is genuinely justified versus when low-level optimization is the cheaper engineering choice. The typical result of this kind of workload optimization is a saving of a few thousand euros per month; in extreme cases it has reached hundreds of thousands of euros per month. The talk is aimed at database engineers, DevOps, software architects, and data engineers.

---

<!-- entries below; newest on top -->

### LAYOUT: long abstracts get ~3 short paragraphs, not one block (confirmed 2026-06)
On a long-form abstract (~300+ words) Ilya manually broke the single block into **three paragraphs** at logical beats: (1) the problem + the FinOps/workload framing; (2) the drivers, the method, and why a routine beats heroics; (3) the takeaway, the concrete examples, and the result + audience line. For anything past ~200 words, propose paragraph breaks at the natural beat boundaries rather than emitting a wall of text. (Supersedes the seeded "1 paragraph, occasionally 2" rule for long-form.)

### DIRECT ADDRESS + say "your Postgres", not "the database" (confirmed 2026-06)
He edited "the database and its workload" → "**your Postgres** and its workload". Two preferences: (a) second-person direct address ("your Postgres", "your servers") over impersonal phrasing; (b) name the product — "Postgres" — rather than the generic "the database" where it reads naturally. Consistent with the existing direct-address voice rule; reinforce it.

### NO REDUNDANT REASSURANCE — state a range once (confirmed 2026-06)
He deleted the trailing clause "…but a couple of thousand a month is the normal, expected outcome." after already saying "typical … a few thousand euros per month; in extreme cases … hundreds of thousands". Once the range is stated, don't re-explain or soften it. Cut the second pass. Concision over reassurance.

### AUDIENCE LINE: his standard set includes DevOps + database engineers (confirmed 2026-06)
He expanded "engineers, software architects, and data engineers" → "**database engineers, DevOps, software architects, and data engineers**." His habitual audience framing leads with database engineers and DevOps (matches his historical talks aimed at "DBAs and DevOps"). When writing the audience line, default to this fuller set unless the topic narrows it.

### RESULT/SAVINGS CLAIMS: state plainly, never as a pitch (confirmed 2026-06)
Real field results (e.g. "saved customers hundreds of thousands of euros per month") are fine to keep — they are genuine experience — but must be stated as a matter-of-fact observation grounded in work done, NOT as a sales pitch. Prefer "in some of the cases we have worked on, optimizing the workload reduced costs by …" over "we have saved customers …". Likewise the audience line should land quietly ("the talk is aimed at …") rather than as a closing flourish. No drama on the numbers.

### VOICE CORRECTION (confirmed 2026-06): precise & technical is the default, wit is occasional
Ilya rejected an aphoristic/poetic register. The default register is **precise, technical, matter-of-fact**. The hook still states the problem up front, but as a concrete technical or operational observation — NOT a literary one. Phrases like "the same animal", "quietly drains the budget", "fix the workload, not the bill" are too literary and were rejected. Dial DOWN the "wry/aphoristic" rule above: wit is occasional flavour, not the default. Dial UP "precise, technical, concrete". When in doubt, prefer the concrete technical statement over the memorable turn of phrase.

### LENGTH: he prefers longer, substantive abstracts (~180–220 words) over compressed ones
For talks where the audience needs to know what they will *see* and *take away*, go to ~180–220 words, not the 80–150 default. "More substance, less compression." Make the itinerary genuinely informative (name the actual tools/drivers/decisions the audience will see) and state the takeaways explicitly. Don't trim itinerary/close to hit a low word count unless a CFP limit forces it.

### TERMINOLOGY: "lock contention", never "lock escalation"
"Lock escalation" is not a proper Postgres concept (it's a SQL Server / DB2 term). Use **lock contention**. Recurring Postgres cost-explosion drivers he names: too many connections, lock contention, unnecessary IO.

### FinOps / cost-per-query framing: treat on-prem and cloud as equivalent, don't center the cloud
FinOps originated in the cloud, but cost-per-query optimization applies to Postgres on-prem and in the cloud almost identically — and that equivalence is the point. Do NOT center the cloud bill. On-prem cost = hardware + self-run HA + backups; cloud cost = instances; both are workload-driven, so fixing the workload beats buying bigger hardware in both. The cloud is just one context, not the subject.
