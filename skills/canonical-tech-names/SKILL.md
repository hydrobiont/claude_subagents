---
name: canonical-tech-names
description: >-
  Correct misspelled or mis-cased technology, product, and project names in
  technical prose so each one is written exactly as the project spells itself —
  PostgreSQL, pgBackRest, ClickHouse, PeerDB, systemd. Use when writing,
  editing, or reviewing any technical text (client write-ups, docs, slides,
  reports, blog posts, emails); when the user asks to "fix tech names",
  "check product spelling", or "normalise terminology"; and as a standing step
  of the Data Egret write-up QA loop together with tighten-prose. Corrects
  prose only — never identifiers inside code blocks, commands, paths, SQL, or
  quoted output (those are exact strings; a mis-cased command is flagged, not
  edited). When a name's canonical form is unknown, it is verified against the
  project's own site/docs/README, never guessed.
---

# Canonical Tech Names

Every technology name in prose is spelled **exactly as the project spells
itself**. Not how it's commonly typed, not how autocorrect renders it, not how
the dictation software heard it — how the vendor or project writes its own name
on its own website.

The rule, in one line: **prose follows the project's branding; code is an exact
string you never touch.**

## The two registers

The same word lives in two registers, and the correction rules are opposite:

1. **Prose register** — the product/project *name* in running text. Follows the
   project's branding: pgBackRest, PostgreSQL, ClickHouse, PgBouncer.
   Misspellings and mis-casings here are corrected.
2. **Code register** — executables, packages, extensions, GUCs, SQL
   identifiers, roles, paths, config keys. These are exact technical strings:
   `pgbackrest backup`, `pg_stat_statements`, `wal_level`, the `postgres`
   superuser. They are **never** "corrected" to branding — `pgBackRest backup`
   does not run on Linux.

The same sentence often uses both: *"pgBackRest stores its config in
`/etc/pgbackrest/pgbackrest.conf`."* Both are correct; neither should be
changed to match the other.

**Reverse catch:** if a *code block* contains a branded form that can't be a
real command (`pgBackRest backup`, `PSQL -c …`), that is likely a real bug in
the doc — **flag it**, but do not edit inside the code block yourself unless
the user confirms.

## The procedure

1. **Scan the prose** (headings, paragraphs, bullets, table cells, image
   captions). Skip everything in the code register: fenced code blocks, inline
   backticks, URLs, file paths, quoted log/command output.
2. **Classify each technology name**: is it in the canonical table below? If
   yes, correct any deviation. If no, **verify** before touching it (see
   Verification). Never "correct" toward a guess.
3. **Apply corrections in place**, keeping a list of what changed.
4. **Flag, don't fix**: ambiguous names, code-register suspects, and deliberate
   informal aliases (see Traps).

## Canonical spellings — seed table

Frequent offenders first. The table is a seed, not a registry — verify anything
absent from it.

### PostgreSQL ecosystem

| Canonical | Commonly mistyped as |
|---|---|
| PostgreSQL | Postgresql, PostgresSQL, PostGres, Postgre, postgreSQL |
| Postgres *(sanctioned informal alias — keep if the doc uses it consistently)* | postgres (as prose name), PostGres |
| pgBackRest | pg_backrest, PgBackrest, pgbackrest (in prose) |
| PgBouncer | pgbouncer (in prose), PGBouncer, pgBouncer |
| Pgpool-II | pgpool, PGPool, pgpool2 |
| pgAdmin | PGAdmin, PgAdmin |
| pgBadger | pg_badger, PgBadger |
| Patroni | patroni (in prose) |
| Barman | barman (in prose) |
| WAL-G | wal-g (in prose), WalG |
| repmgr *(always lowercase)* | RepMgr, Repmgr |
| pgvector *(always lowercase)* | PGVector, PgVector |
| pg_repack, pg_partman, pg_stat_statements, pg_dump, pg_basebackup, psql, pgbench *(always lowercase, usually backticked — they name the artifact itself)* | Pg_dump, PSQL, PgBench |
| PostGIS | PostGis, Postgis |
| TimescaleDB | TimeScaleDB, Timescale DB |
| Citus | citus (in prose) |
| PL/pgSQL | plpgsql (in prose), PL/PgSQL |

### Databases & data infrastructure

| Canonical | Commonly mistyped as |
|---|---|
| ClickHouse | Clickhouse, Click House, clickhouse (in prose) |
| ClickHouse Cloud, ClickPipes | Clickhouse Cloud, Click Pipes, Clickpipes |
| PeerDB | PeerDb, Peerdb, peerDB |
| MySQL | MySql, mySQL |
| MariaDB | MariaDb, Maria DB |
| SQLite | SQLLite, SqlLite, Sqlite |
| MongoDB | MongoDb, Mongo DB |
| Redis / Valkey | redis (in prose), ValKey |
| Elasticsearch | ElasticSearch, Elastic Search |
| OpenSearch | Opensearch |
| Apache Kafka | Kafka (first mention; bare Kafka fine after), kafka |
| Apache ZooKeeper | Zookeeper, ZooKeeper without Apache on first formal mention |
| Debezium | debezium (in prose) |
| Microsoft SQL Server | MSSQL (informal; fine in internal notes), MS SQL Server |
| Oracle Database | oracle (in prose) |

### Cloud & infrastructure

| Canonical | Commonly mistyped as |
|---|---|
| AWS; Amazon EC2, Amazon S3, Amazon RDS, Amazon Aurora, CloudWatch, IAM *(bare EC2/S3/RDS fine after first mention or in internal notes)* | Ec2, s3 (in prose), Rds |
| Google Cloud (GCP), Cloud SQL, BigQuery | Google cloud, CloudSQL, Big Query |
| Microsoft Azure | MS Azure, azure |
| Kubernetes *(K8s informal)* | kubernetes (in prose), k8s in formal deliverables |
| Docker, Docker Compose *(the v1 binary was `docker-compose`)* | docker (in prose), docker compose (as a name) |
| Terraform, OpenTofu | terraform (in prose), OpenTOFU, Opentofu |
| Ansible | ansible (in prose) |
| HAProxy | HAproxy, HaProxy, haproxy (in prose) |
| Keepalived | KeepAlived |
| systemd *(always lowercase, even at sentence start — rephrase instead of capitalising)* | Systemd, SystemD |
| etcd *(always lowercase, same rule)* | Etcd, ETCD |
| nginx *(project site) / NGINX (F5 branding) — pick one per document, consistently* | Nginx |
| MinIO | Minio, MinIo |
| ZFS, XFS, ext4, Btrfs | Ext4, BTRFS, btrfs (in prose) |

### Observability & tooling

| Canonical | Commonly mistyped as |
|---|---|
| Grafana, Prometheus, Zabbix | grafana, prometheus (in prose) |
| OpenTelemetry (OTLP) | Open Telemetry, OpenTelemetry Protocol misorderings |
| Datadog | DataDog, Data Dog |
| PagerDuty | Pagerduty |
| GitHub, GitLab | Github, Gitlab |
| Git *(the system; the command is `git`)* | git (in prose), GIT |
| Jira, Jira Service Management, Tempo | JIRA (pre-2017 branding), Jira ITSM (informal) |
| Odoo, Pipedrive, easybill *(lowercase by brand)* | ODOO, PipeDrive, Easybill |
| WordPress, Elementor, Yoast SEO, Polylang | Wordpress, WordPress without capital P |
| YubiKey | Yubikey, YubiKey miscased as yubikey in prose |
| Node.js | NodeJS, Node.JS, nodejs |
| JavaScript, TypeScript | Javascript, Typescript |
| Python, Go *(Golang only informally)*, Rust, Java | python (in prose), GoLang |
| reveal.js *(lowercase by project)* | Reveal.js, RevealJS |
| Pandoc *(prose; the command is `pandoc`)* | pandoc (in prose) |
| macOS, Linux, Ubuntu, Debian, Red Hat Enterprise Linux (RHEL), Rocky Linux, AlmaLinux | MacOS, OSX, linux (in prose), RedHat, Alma Linux |

## Traps

- **"Postgres" is not a typo.** It's the community-sanctioned informal alias.
  Leave it where the document's register is informal; only align it to
  PostgreSQL in formal deliverables, and then consistently — never mid-document
  flip-flopping.
- **Role vs product:** "the `postgres` superuser", "the `postgres` binary" are
  code register. "Postgres replicates…" is prose register.
- **Sentence-start lowercase names** (systemd, etcd, pgvector, psql): the
  projects keep them lowercase even there. Rephrase the sentence rather than
  capitalising the name.
- **Quoted material is untouchable.** Log lines, error messages, command
  output, and direct quotes keep their original spelling — even when wrong.
- **Acronym case:** WAL, MVCC, CDC, TTL, TLS, SSL, JSONB, DDL, DML — all caps;
  never "Wal files" or "jsonb column" in prose (the *type* `jsonb` in backticks
  is code register).
- **Don't expand scope.** This is a spelling pass, not a terminology rewrite —
  changing "DB" to "database" or "K8s" to "Kubernetes" is a style decision for
  the author or tighten-prose, not this skill (the K8s row above applies to
  formal deliverables only).

## Verification (names not in the table)

Branding is checked against, in order:

1. The project's **own website** — masthead, title, footer.
2. The project's **official docs** or FAQ (some, like systemd, state the
   casing rule explicitly).
3. The **README in the canonical source repository**.

Wikipedia, blog posts, and package names (`apt install pgbackrest`) are **not**
authorities — packages are code register. If sources genuinely disagree (the
nginx case), pick the project's own form, apply it consistently, and note the
choice. If you cannot verify, **flag instead of changing** — a wrong
"correction" is worse than a flagged unknown.

When you verify a name worth keeping, propose a table addition in your report —
the user curates this file; don't grow the table silently.

## Output

- **Applied corrections**, compact: `pg_backrest → pgBackRest (3×)`,
  `Clickhouse → ClickHouse (7×)`. Don't narrate each occurrence.
- **Flags**: code-register suspects (mis-cased commands in code blocks),
  unverifiable names with the candidate forms, deliberate-alias judgement calls
  (Postgres vs PostgreSQL register).
- **Nothing else changes.** This pass rewrites no sentences, drops no words,
  and never alters meaning — pure name normalisation. Word economy is
  `tighten-prose`'s job; run the two together in the QA loop, this one last so
  tightening can't reintroduce a mis-spelling it never saw.
