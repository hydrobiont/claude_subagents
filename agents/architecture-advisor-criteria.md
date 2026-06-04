# Architecture Advisor — Evaluation Criteria

This is the rubric the `architecture-advisor` agent uses when evaluating technologies, frameworks, libraries, formats, or architectural approaches.

Apply only the sections relevant to the decision being researched. The **Universal** section applies to nearly every decision. The **Red flags** and **Anti-criteria** sections always apply.

This file is meant to evolve. After every research run the agent proposes 0–2 additions or refinements; ik@dataegret.com approves before they land here.

---

## Universal (applies to almost every decision)

### Maturity & maintenance
- Project age and date of first stable (1.0+) release
- Last release date and real release cadence (count human-tagged releases, not bot bumps)
- Commit cadence over the last 6–12 months
- Number of active contributors and bus factor (solo maintainer is a red flag, not an automatic disqualifier)
- Single-maintainer commit dominance ratio (top contributor's commits ÷ second-place's). Ratio > 20× signals a hidden solo project even when stars and release cadence look healthy.
  - *Why:* `jackc/pgx` (3140 : 54) and `sfackler/rust-postgres` (2529 : 94) both look healthy by other metrics but are functionally one-person projects. Raw contributor count hid that.
- Backed by a company, foundation, or volunteer maintainer? If company-backed, is the company healthy?
- On a stable major version or still in pre-1.0 flux?

### Community health
- Issue activity: open-vs-closed ratio, response time, are stale issues triaged?
- Number of contributors with merged PRs in the last 12 months
- Forum / Slack / Discord / mailing-list activity — actual help happening, not vanity metric
- Stack Overflow / Discourse / Reddit signal for the tag
- GitHub stars treated as a weak signal only

### Production-readiness
- Named, verifiable production adopters (blog posts, conference talks, case studies — not "logos on the homepage")
- License, and license history — recent rugpulls are a major red flag (HashiCorp, Elastic, MongoDB, Redis Labs)
- Security track record: CVEs reported, response time, public security policy
- API stability — does every minor release break things?

### Developer experience
- Documentation quality (fresh, accurate, covers real workflows, not just hello-world)
- Time-to-first-useful-result for a competent engineer new to the tool
- Debuggability (clear error messages, observable internals, readable source)
- Testability (mocks / fakes available, integration test story)
- IDE / tooling support

### Operational fit
- Observability story (metrics, logs, tracing) — out of the box or DIY?
- Operational complexity — how many moving parts to keep healthy
- Compatibility with existing stack (avoid introducing a parallel ecosystem when one is already in use)
- Day-2 ops: patching, upgrading, backup / restore (for stateful systems)

### Performance
- Independent benchmarks (with skepticism: who, what hardware, what workload?)
- Scalability characteristics — vertical, horizontal, and where it falls over
- Resource footprint (CPU, RAM, disk)

### Lock-in & exit
- Standards-based vs proprietary
- Data portability — can the user get their data / state out?
- Migration story away from it — what would it take to leave?

### Cost
- License / subscription cost
- Operational cost (infra, compute, storage)
- Engineering time to adopt, and to operate

---

## Databases, storage, PostgreSQL extensions

- PostgreSQL version support range — must include the version the user runs
- Replication compatibility (logical and physical)
- Works under connection poolers — **pgBouncer transaction mode is the hard test**
- Hot-upgrade / online schema change story
- AGPL / GPL viral concerns for extensions linked into the backend
- Maintained by a known PG community member? Listed on PGXN? Packaged for Debian / RHEL?
- For PG extensions specifically: does it require `shared_preload_libraries` + restart, or install-on-the-fly?
- For data stores: write-path durability guarantees (fsync, group commit, replication semantics)
- For data stores: consistency model (linearizable, causal, eventual) — and is it clearly documented?
- Backup compatibility (`pg_dump`, physical, WAL-based) — does the extension survive a restore?

---

## Infrastructure, deployment, observability

- Self-hosted vs SaaS-only vs both
- HA / failover story (active-active, active-passive, manual?)
- Multi-region / multi-AZ support
- IaC support — Terraform / OpenTofu provider, first-party or community?
- Day-2 ops: rolling upgrade, patching, capacity planning
- Integration with existing telemetry (OTLP, Prometheus exposition, etc.)
- Cardinality / retention limits (for metrics / logs / traces backends)
- Authentication & RBAC — OIDC, SAML, scoped tokens?
- Audit log support if compliance matters

---

## Frontend / UI tooling

- Bundle size impact with a realistic feature set (not the hello-world number on the homepage)
- Browser support matrix vs target audience
- SSR / SSG support if needed
- Accessibility primitives (focus management, ARIA, keyboard nav) — first-class or bolt-on?
- Build-tool integration (Vite, esbuild, Webpack, …)
- Styling story (CSS-in-JS, utility CSS, CSS Modules, Shadow DOM)
- Ecosystem maturity (form libs, routing, state, data-fetching) — vibrant or DIY-everything?
- Time-to-hydrate / time-to-interactive for the typical page

---

## Formats, wire protocols, APIs

- Spec stability tier — Standard / Stable / Beta / Development. Where does it live (RFC, IETF, Apache, vendor doc, GitHub README)? "Development"-tier formats can change wire shape and external tools won't yet decode them.
  - *Why:* OTel File Exporter spec looked attractive ("standard OTel format on disk") until "Development" status surfaced — committing would mean chasing changes. The user prefers Standard / Stable for formats.
- Schema evolution story — forward/backward compatibility rules
- Tooling ecosystem (codegen, validators, linters, conformance test suites)
- Vendor neutrality — single-vendor format implies lock-in
- Encoding overhead (size on wire, parse cost)
- Human-readable vs binary tradeoff for the use case
- Adoption — who actually emits and consumes it in production?
- For OTel-flavoured formats specifically: which collectors / backends accept it without translation?
- Live concurrent read while a writer is appending — can a second process query the in-flight file with arbitrary indexed/time-range queries? SQLite (WAL) yes; Parquet no (row-group flush boundary makes the tail invisible); JSONL yes-but-sequential; CSV yes-but-sequential.
  - *Why:* Decided the audit-tool bundle format (SQLite WAL) over Parquet for the live-viewer use case — Parquet's row-group cadence would have left the last 8–10 min of a 1-hour run invisible to the viewer.

---

## Language ecosystem / dev tooling

- Compatibility with the target language runtime version
- Plays nicely with the project's existing toolchain (lockfile format, virtual envs, build cache)
- Migration cost from the incumbent tool (lockfile import, CI changes, contributor friction)
- CI integration — official actions / images, or roll-your-own?
- Cross-platform (macOS / Linux / Windows) support if the team is mixed

---

## Red flags (apply to every decision)

These don't auto-disqualify a candidate, but they must appear in the report:

- **Solo maintainer** with no co-maintainer named anywhere in the repo or org
- **Last release > 12 months ago** with no explanation ("done" is fine if stated explicitly)
- **Major breaking changes every release** without a stabilization roadmap
- **Star count >> production adopters** — toy project with hype
- **License changed in the last 24 months** in a more-restrictive direction
- **Closed governance, single vendor** with no public roadmap or RFC process
- **Documentation visibly written by AI** without expert review (hallucinated APIs, broken examples)
- **Vendor benchmarks** that beat every competitor on every axis
- **"Production-ready" / "battle-tested"** with no named user
- **Reinvents an established standard** without a clearly stated reason
- **Depends on an abandoned upstream** that hasn't been forked / replaced
- **High Twitter / HN buzz, low Stack Overflow / mailing-list activity** — talking, not using
- **Telemetry / phone-home on by default** without an obvious off switch
- **CLA required for trivial contributions** signals corporate control intent

---

## Anti-criteria (signals that look bad but usually aren't)

- **Low star count + long history + steady maintenance** → "boring tech", usually a positive
- **Few releases per year** → sometimes "done", not "abandoned" — check the issue tracker, not just tags
- **Small team** → fine if the team is responsive and the scope is narrow
- **No SaaS option** → sometimes a feature; self-host-first projects often have healthier OSS communities
- **Sparse marketing site** → often correlates with engineering culture > marketing culture
- **Mailing list instead of Discord** → not dead, just older — typical of high-quality infra projects
- **Recent CVE that got rapidly fixed** → signal of project popularity + maintainer responsiveness, not a flag. Zero CVEs on a low-attention project is not better.
- **Not on a curated archival-format list** (e.g. Library of Congress recommended formats) → weak negative signal unless 20-year readability is an actual requirement. De facto industry adoption (Parquet, Arrow, modern columnar formats) is the stronger axis for short/medium-term use.

---

## How to extend this file

After each research run the agent proposes 0–2 additions. Format:

    - <criterion stated as a one-line check>
      - *Why:* <one line — what made you notice it>

Place the addition under the most-relevant section. Create a new section only if no existing one fits.

Keep this file a **checklist, not an essay**. If a criterion needs paragraphs to explain, split it into two criteria.
