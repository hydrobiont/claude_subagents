---
name: claude-md-architect
description: >-
  Keep CLAUDE.md files lean by carrying only what's needed every session and moving
  task-specific detail into referenced files that load on demand. Use when creating a
  new CLAUDE.md, when one has grown large or unwieldy, or when the user asks to slim,
  refactor, split, shrink, or reorganize a CLAUDE.md — "make CLAUDE.md smaller",
  "reference files instead of inlining everything", "keep CLAUDE.md lean", "break this
  up into on-demand files", or set up a docs/ folder of guides read only when relevant.
  Applies the every-session-vs-on-demand split, extracts detail into docs/<topic>.md,
  and leaves one-line pointers carrying read-when triggers. Complements /init (which
  generates a CLAUDE.md) by enforcing the lean-core discipline on top of it.
---

# CLAUDE.md Architect

A `CLAUDE.md` is injected into context **at the start of every session** and stays there
for the whole conversation. Every line in it is paid for on every turn. So the file should
carry only what's needed *every* session — and hand everything else to files that are read
*only when the task calls for them*.

The rule, in one line: **if a block is needed every session, keep it in the core; if it's
needed only when working on X, move it to a referenced file with a "read when X" trigger.**

## The split test

For each section/block, ask: *"Do I need this every session, or only when working on a
specific part of the project?"*

**Stays in the lean core** (needed every session):
- What the project is + current status — a line or two.
- How to build, test, run, lint — the commands.
- The **big-picture architecture** — the cross-cutting shape you only get by reading several
  files; the thing someone must hold in their head to be productive.
- Hard rules / conventions that apply broadly (secrets handling, commit rules, house style).
- The **index of on-demand references** (below).

**Moves to an on-demand file** (needed only for a specific task):
- Per-subsystem or per-module deep dives.
- API / field / schema references (e.g. an integration's exact field map).
- Platform- or service-specific detail (one file per integration).
- Interface / spec / design documents.
- Runbooks and step-by-step procedures.
- Long catalogs of gotchas, edge cases, or version notes.

When in doubt, move it out — the core should read top-to-bottom as a quick brief.

## Pointer format

In the core, each extracted topic becomes one line that says **what it is and when to read it**:

```
- [docs/odoo.md](docs/odoo.md) — read when touching the Odoo/ticketing integration.
- [docs/interface.md](docs/interface.md) — read when changing the command surface.
```

- On-demand files live in a `docs/` subdir next to the `CLAUDE.md` (or any subdir — keep it consistent).
- Use **repo-relative** links so they resolve in the repo and are clickable.
- The trigger is mandatory — a pointer without a "read when …" is just a file list.

## Procedure

**Refactoring an existing CLAUDE.md:**
1. Read it; list its sections/blocks.
2. Classify each block with the split test: core vs on-demand.
3. Group the on-demand blocks by topic. For each, create or append `docs/<topic>.md` and move
   the detail there (tighten while moving if helpful, but preserve the claims).
4. In the core, replace each moved block with a one-line pointer + read-when trigger.
5. Confirm the core still holds orientation, commands, architecture, rules, and the reference
   index — and nothing task-specific.
6. Verify: no fact is duplicated between core and a doc (each lives in exactly one place);
   every link resolves.

**Creating a new CLAUDE.md** (e.g. after `/init`): sort facts as you gather them — essentials
into the core, deep detail straight into `docs/<topic>.md` behind a pointer. Build it lean;
don't write a big file and split it later.

## Size guidance

No hard line limit — the test is the split, not a number. A healthy core reads in a screen or
two. If a section runs more than a few lines of task-specific detail, that's the signal to
extract it. A 9 KB core full of API field tables is a smell; a 9 KB core that is all
big-picture architecture may be fine.

## Guardrails

- **Don't move the essentials out.** Build/test/run commands, the big-picture architecture,
  and broadly-applicable rules are needed every session — they belong in the core.
- **Don't duplicate.** A fact lives in one place: the core points, the doc holds.
- **Don't fabricate** detail to fill a doc — only relocate content that already exists.
- **Keep links relative and clickable**, and give every pointer its trigger.
- **Preserve meaning** when moving text — extraction is relocation, not re-litigating claims.

## Worked example

The `data-egret-slack-bot` project: a lean `CLAUDE.md` (orientation, status, big-picture
architecture, decisions, conventions) that points to `docs/interface.md`, `docs/slack.md`,
`docs/teams.md`, `docs/odoo.md` — each read only when working on that surface. The Odoo field
maps and the full interface spec never load unless you're touching those areas.
