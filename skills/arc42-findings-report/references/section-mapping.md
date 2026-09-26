# Section mapping: where a finding goes

Template: `~/work/de/clients/arc42_postgres_tmpl/workshop.md`. Sections and order are fixed;
subsections come from the template and are dropped when empty. The user decides unclear
placements; the table gives the default proposal.

| Finding type | Section | Subsection | Notes |
|---|---|---|---|
| What we observed in the system (versions, sizes, object counts, topology, settings) | Introduction and goals | Current architecture and setup | Facts with source (analysis file, command, document); dates in ISO form |
| What the customer told us (problems, incidents, complaints, history) | Introduction and goals | Issue history from the customer | Grouped by topic as the template comment lists |
| What the customer wants (targets, constraints they impose, scope statements) | Introduction and goals | Requirements overview (user stories and use cases) | As user stories: "We need to ... because ..."; the pipeline the customer prescribes is a user story and a constraint at the same time: state it here, reference it in Architecture constraints |
| Quality goals (ISO 25010 wording) | Introduction and goals | Goals of improvement | Three to five; ask if none stated |
| People and their expectations | Introduction and goals | Stakeholders | Ask; never invent |
| Access, environments, channels, dates | Work organisation | Access, Communication | Ask if missing |
| Given limits: regulation, platform standards, licences, timelines, "no connection to X" | Context and scope | Architecture constraints, Timing / timeline | Constraints are given, not chosen |
| Measured technical facts from discovery (schema statistics, type mapping, data volumes, LOB sizes, verification tables) | Context and scope | Technical findings (discovery) | Use the template's subsections where they fit (Schema design, Workload, HA setup, Backup and recovery setup) and add a subsection for other facts (for example "Data volume and types"); full tables inline |
| Variants, comparisons, tool evaluations, recommended procedure, settings, measurement plan | Solution strategy | one subsection per variant or topic | Per item: solution, goals addressed, alternatives considered, risks, split of work customer/Data Egret, effort (S/M/L), priority (Now/Next/Later), dependencies; the recommendation is stated but stays a recommendation |
| Configuration, troubleshooting, observability advice | Solution strategy | the three template subsections | Fields as in the template comments |
| Anything unresolved or dependent on a customer or vendor answer | Open items | grouped by who answers (customer team, vendor, us) | Written as questions; removed once answered in Solution strategy |
| A way of working assumed during the analysis but not decided by the customer (for example how the migration is organised: direct connection or files) | Solution strategy as variants with a comparison table and decision criteria, plus Open items under "Decision to take with the customer" | | Never state the assumption as a constraint or as a customer statement; the customer decides after the measurements |
| Agreed with the customer | Decisions | one entry per decision | Context, decision, alternatives, rationale, consequences; nothing proposed lands here |
| Risks, technical debt, known gaps | Risks and technical debts | list ordered by priority | Description, impact H/M/L, likelihood H/M/L, priority P1..P3, mitigation, owner |
| Terms, abbreviations, product names | Glossary (appended by the scaffold) | alphabetical | One concept, one term; source per definition where one exists |

## Worked example: the G104 migration findings (Boehringer Ingelheim, 2026)

| Finding | Placement |
|---|---|
| Oracle 19c EE RU 19.28, Data Pump export properties, PostgreSQL 14.22 vendor dump, schema and object counts, row-count agreement between the dumps | Introduction and goals, Current architecture and setup |
| Target platform (PostgreSQL 18, RHEL 9, Patroni, synchronous replication) from the July 2026 workshop | Introduction and goals, Current architecture and setup |
| "Export on the production server, move files, load from the migration host, no Oracle connection from that host" | Requirements overview as a user story; repeated as an Architecture constraint |
| GxP change control, Körber delivers the schema, PostgreSQL 14 end of life | Architecture constraints |
| Type mapping matrix, LOB sizes, hidden columns, NOT NULL drift, sequences, FK and index counts, COPY text volume | Technical findings (discovery), subsection "Schema design" and a new subsection "Data volume and types" |
| Exporter comparison, loader comparison, recommended procedure, load-window settings, measurement plan | Solution strategy, one subsection each |
| Which tables without a target may be dropped, PAS-X support for PostgreSQL 18, scope of the other schemas, footprint allowed on the production server | Open items, grouped "Questions for Körber" and "Questions for the platform team" |
| Nothing agreed yet | Decisions stays empty with its template comment |
| Precision loss FLOAT to double precision, bigint narrowing, NUL bytes, export inside the window, single large table | Risks and technical debts |
