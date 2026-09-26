# Files, frontmatter, snapshots

## Location and name

`~/work/de/clients/<customer>_internal/<year>/<TICKET>.md`, where `<TICKET>` is the Odoo
ticket ID the user gives. Without a ticket from a human, use a meaningful lower-case name
with hyphens (for example `g104-oracle-to-postgresql-data-migration.md`). One report per
ticket. Add a link line to the client `Readme.md` under the year. Never run git commands in
the client repository; the user reviews and commits.

## Frontmatter (Data Egret converter)

```
---
title: "<Customer legal name> — <topic>"
author: "Data Egret (Firstname Lastname[, Firstname Lastname])"
date: "17 September 2026 (Thursday)" # LC_TIME=C date +"%d %B %Y (%A)"
...
```

The block closes with `...` as in the template. The template's first H1 follows the
frontmatter; `client-report-builder` warns about a leading H1 because the cover title comes
from `title:`; keep the template's structure and accept the warning, or remove the H1 when
compiling if the user prefers.

## Comments

The template's HTML comments are working checklists. They stay in the working file. Version
snapshots (`<name>-vX.Y.md`) and compiled outputs carry none: `scripts/scaffold_report.py
snapshot IN OUT` strips them. Example text marked "delete before use" is removed in the
working file already.

## Snapshot

Only when the user declares a version: write `<TICKET>-vX.Y.md` next to the working file,
without comments, and report the path. Compilation to HTML and PDF is `client-report-builder`'s
job and a separate request.
