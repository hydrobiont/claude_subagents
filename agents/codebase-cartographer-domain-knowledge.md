# Codebase Cartographer — Domain knowledge

Persistent notes accumulated by the `codebase-cartographer` agent across invocations. The agent reads this file at the start of every run and appends entries when it learns something durable about the domain — e.g. signals that reliably identify a repo's build system, patterns for spotting fork/upstream relationships, repository structures the user works with repeatedly, file paths that consistently hold load-bearing context, etc.

See the agent definition (`codebase-cartographer.md`) for the rules on what belongs here vs not.

<!-- entries below; newest on top -->

### Sibling-repo extensions can blow past the 400-line cap

When the user asks for a new repo block in an existing parent-level `CLAUDE.md`
and explicitly requires "match the depth and style" of an existing block,
treat the depth requirement as overriding the 400-line guidance. Match the
neighbour block's section length (count lines: `awk '/^### /{p=NR}/^## /&&p{print NR-p; exit}'`)
rather than trying to compress. The user authored the existing depth, so they
have demonstrated the preference. Still aim to trim padded prose and defer
long enumerations to the repo's own docs (e.g. point at `DONE.md` /
`pgcluu_collectd:135-413` instead of re-listing every metric).
