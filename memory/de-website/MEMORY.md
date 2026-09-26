# Project Memory — dataegret.com Website

## Project Manager Agent
A dedicated sub-agent **`de-website-manager`** (model: opus) leads this project end-to-end: theme/PHP development, the dev→staging→prod deploy pipeline, Elementor operations, and SEO/GA4/Google-Ads/SERP coordination. Route website work to it via the Agent tool. It is seeded with a full code+infra+strategy map in `~/.claude/agents/de-website-manager-domain-knowledge.md` and reads this MEMORY.md each run. It does code/DB/deploy/analytics itself, and delegates live browser-UI to `browser-operator` and long-form writing to the `technical-writer` skill.

## Deployment Workflow
development (localhost) → staging (dev2.dataegret.com) → production (dataegret.com)

- **Development**: Docker on localhost:8080 (`dataegret_wordpress` container) — this is "local"
- **Staging**: dev2.dataegret.com (SSH port 50222) — verify with Google Analytics here
- **Production**: dataegret.com (SSH port 50202)

## Repository
Path: `/Users/ik/work/de/website/de-website-3`
Custom theme: `wp-content/themes/data-egret/`

## Site Structure
- Multilingual: en-GB (primary), de-DE, ru-RU — using **Polylang** plugin
- Page builder: **Elementor** + Elementor Pro
- Custom theme: `data-egret` (custom PHP/JS, not a child theme)
- Key plugins: ACF Pro, Contact Form 7, Polylang, **Yoast (the active SEO plugin)**, **Complianz (the active consent banner)**, Custom Post Type UI. AIOSEO + Real Cookie Banner are installed but **inactive** (verified 2026-08-12)

## Google Analytics & GTM Setup
GTM and GA4 are hardcoded in `header.php`, switched by language (`get_bloginfo('language')`):

| Language | GA4 ID | GTM Container |
|---|---|---|
| en-GB (staging dev2) | G-P3XRY2D4FB | GTM-5XTQZXB |
| en-GB (production) | G-PLXB9VHN7B | GTM-5XTQZXB |
| de-DE | G-0S38VWLP7K | GTM-WFZ85BX |
| ru-RU | — | — (removed, not in use) |

GA4 property IDs (Analytics API):
- `dataegret.com - GA4`: properties/356651240 (G-PLXB9VHN7B, en production)
- `dev2.dataegret.com`: properties/526891673 (G-P3XRY2D4FB, en staging)

Host gating: since `1af34fa`, analytics are deny-by-default via `de_analytics_mode()` + `de_production_hosts()` allowlist in `environment-config.php` (header.php fail-closed).

## Custom Event Tracking
`js/ga-events.js`: `panel_open`, `phone_click`, `email_click`, `form_submit` (CF7 IDs: 159=Contact EN, 1576=Join Team EN, 1399=Contact DE), `page_not_found`.

## Existing GA4 Custom Dimensions (dataegret.com - GA4)
cf7_status_message, contact_reason, discovered, formID, gtm_container,
no_postgresql_installation, os_selected, postgresql_version,
**content_category**, **content_topic**, **page_type**

Content dimensions are event-scoped, computed in `functions.php` (`de_get_datalayer_vars()`),
and passed to GA4 via `gtag('config', id, params)` in `header.php`.
- `content_category`: homepage / blog / service / landing / page / hub / about / 404 / search
- `content_topic`: performance / replication / backup / data-analytics / migration / monitoring / connection-pooling / tools / other
- `page_type`: landing / article / archive / 404

## Server Access
- **Gateway host is `svc2.pgco.me` (5.9.102.135) — NOT `svc.pgco.me`** (corrected + verified live 2026-08-10; the old host still resolves but no longer serves :50222/:50202, giving a misleading `Network is unreachable`). Repo docs (`CLAUDE.md`, `INFRASTRUCTURE.md`) are still stale on this.
- Production SSH: `ssh -p 50202 ik@svc2.pgco.me` — hardware YubiKey required; no askpass, so a *direct* invocation cannot run unattended. **But one PIN goes a long way:** ask the user to open a ControlMaster (`ssh -fNM -S ~/.ssh/ctl-prod -o ServerAliveInterval=30 -p 50202 ik@svc2.pgco.me`), then every later `ssh -S ~/.ssh/ctl-prod ik@svc2.pgco.me 'cmd'` needs no prompt. **Trap:** `-fNM` fails if the socket file already exists (dead ones get left behind when a session skips `-O exit`) — `rm -f ~/.ssh/ctl-prod` first. Details: [Server access](de_website_ssh_access.md)
- Staging SSH: `ssh -p 50222 ik@svc2.pgco.me` — **works unattended**; ignore the pkcs11/askpass stderr noise, auth falls through to a working key. Needs `dangerouslyDisableSandbox` (non-standard port).
- WP root (both servers): `/data/www/blog`
- DB credentials: `mysql -u wordpressuser -pwppasswordwp blog`
- WP-CLI: staging only (`/usr/local/bin/wp`), NOT installed on production
- Full infra docs: `de-website-3/INFRASTRUCTURE.md`

## Elementor — canvas/template/cache issues
- [Canvas issues & fixes](elementor_canvas_issues.md) — template-lock hook (`de_lock_elementor_full_template`), the mandatory trifecta (`_wp_page_template` + delete `_elementor_element_cache` + `_elementor_css`), safe JSON write-back (UNHEX / SQL REPLACE, never `$wpdb->update` — `%` breaks prepare), affected post IDs
- [Unclosed HTML tags in widgets](elementor_unclosed_html_tags.md) — nested-section symptom; detection + repair recipe

## Collaboration Preferences
- [No co-author in commits](feedback_no_coauthor.md) — never add Co-Authored-By Claude line
- [Never touch out-of-scope hosts](feedback_no_out_of_scope_hosts.md) — ask explicitly; don't infer a bastion or route around a blocked path
- [Server access, canonical](de_website_ssh_access.md) — `svc2.pgco.me`; staging runs unattended via `~/.ssh/id_rsa`, production needs one PIN then a ControlMaster; stale-socket trap
- [Never edit Elementor text widgets via TinyMCE](feedback_no_tinymce_editing.md) — it strips `<style>` blocks and mangles card HTML; edit `_elementor_data` JSON instead
- [Buyer intent ≠ blog traffic](seo_buyer_intent_insight.md) — blog readers are practitioners, not buyers; landing pages must target buyer queries
- [Stripe: designated sandbox ONLY](feedback_stripe_sandbox_only.md) — never live mode or other sandboxes; verify context first; sk_test_ assertion off-prod; also in agent domain knowledge

## Deployment Schema (decided 2026-06-10)
**CI-only SSH, scoped keys** — no manual SSH for deploys. Staging: `deploy-staging.yml` now also ships `wp-content/mu-plugins/` (rsync **without** `--delete`; backup + perms included). Pending Phase 2: scoped `deploy-stg`/`deploy-prod` users replace the personal `ik` key in GitHub Secrets; new `deploy-production.yml` gated by a `production` GitHub environment (org plan `team` supports required reviewers). Bump `actions/checkout@v4`/`ssh-agent@v0.9.0` before 2026-06-16 (Node 24 forced).
**Hazard**: `scripts/deploy.sh` deploys the *working tree* — servers can be ahead of git. Always commit theme drift before pushing `staging` (the April course sprint was recovered into commit `dbbbf23` this way).

## Popup CPT & dead-URL redirects (2026-06-10)
- `mu-plugins/popup-cpt-visibility.php`: popup CPT is non-public (`publicly_queryable=false`, `rewrite=false`, `query_var=false` + option-guarded one-time `flush_rewrite_rules()`). Footer modals unaffected (rendered inline via WP_Query); Yoast dropped `popup-sitemap.xml` automatically. **Gotcha**: without `rewrite=false`+flush, stale rewrite rules make `/popup/<slug>/` canonical-301 to home and `is_404()` handlers never fire. Code-level flush is mandatory — production has no WP-CLI.
- `mu-plugins/redirects.php`: rawurldecodes paths (Cyrillic slugs); 301 map for dead popups / `/ultimate-plan/` / `/ru/` / `/en/` / `resourses` typo; **410 catch-all** for any other `/popup/*`.
- GSC baseline 2026-06: 287 indexed / 507 not-indexed; the Jun 1+9 notifications were popup-404s + dev2 sitemap noise (domain property `sc-domain:dataegret.com` covers subdomains). Full detail in `~/.claude/agents/de-website-manager-domain-knowledge.md`.

## Blog Syndication
- [Planet PostgreSQL syndication](planet_postgresql_syndication.md) — Planet pulls 9 **core** per-author `/category/<slug>/feed/` URLs; WP RSS Aggregator is unrelated + vestigial. Protect the slugs, they fail silently.

## Database Volume
- [Database bloat findings](database_bloat_findings.md) — DB is 97.9% junk (spam comments + Elementor revision copies); 1,137 MB → 24 MB verified cleanup recipe

## Comment spam / W1 — DONE both environments 2026-08-10
- [Antispam Bee option is corrupt](antispam_bee_option_corrupt.md) — real cause of the 177k spam backlog; repair the option, not the cron hook. **Shipped:** 781.9 MB reclaimed on staging, 741.5 MB on production; cron verified firing. Retention still 30 d (7 d recommended).
- Session handoff: `de-website-3/HANDOFF-2026-08-10.md`; reusable scripts in `de-website-3/scripts/w1-*.sh`

## WordPress.com migration PoC — DB IMPORT DONE (2026-08-13); FULL gate pending
- [Status, posture, remaining steps, platform lessons](wpcom_poc_status.md) — read FIRST when resuming; points to handoff doc, the authoritative CHANGES-DB 2026-08-13 import entry, parity-delta ledger, and committed baseline
- Hard rails: production untouchable; no DNS changes; never press wpcom "Sync"; test-spec artifact = the contract (SAFE/SMK/DBI/FULL)
- Target `staging-7eb1-dataegret.wpcomstaging.com` (PHP 8.4); push `staging` deploys dev2 AND wpcom staging (merge-no-delete)

## Course Booking → Odoo integration (spec v1.1, WP side reviewed 2026-08-15)
- Contract: `de-website-3/specs/booking-integration-spec.md` (A = system contract, B = Odoo module, C = test suites, D = the four-loop dev cycle). WP side = mu-plugin `de-booking-bridge.php`, theme template `page-course-booking.php` (`/book/`), L1 runner `tests/booking/run-book-suite.sh`.
- **One intake only**: REST `POST /wp-json/de/v1/booking`. The unused Elementor form path was removed in bridge 0.2.0 — a second intake path is a defect (the two had already drifted apart).
- `course_code` = the WordPress **page slug** (`courses-postgresql-essentials-dba1`), never `dba1`. Applies to every fixture too.
- Bridge **0.2.0**: 429 = retryable throttle (queue + back-off, same `booking_ref`, `Retry-After` honored as a *floor*, capped 1 h); every other 4xx terminal. **Odoo must keep signalling overload with 503 until a ≥ 0.2.0 bridge is actually deployed** — read the deployed version with `wp de-booking status`.
- DB-only per environment (recipe in `CHANGES-DB.md`): the `/book/` page + `_wp_page_template=page-course-booking.php`, and options `de_booking_enabled` / `de_booking_endpoint` / `de_booking_secret` (**values never in git**). Live on **wpcom staging only** — dev2 404s, production has neither.
- `/book/` is a native PHP template, not Elementor: no cache trifecta, and its slug must never enter `de_locked_full_template_slugs()` (that hook would force `page-elementor-full.php` over it on every save).
- Version-controlled mu-plugins are now **6** (SMK-04's expected count).

## Active Plans
- [Google Ads campaign plan](google_ads_plan.md) — €20/day test budget for 3 DBA courses; campaigns stay paused until verification completes
- Remediation Plan (Aug 2026): `de-website-3/REMEDIATION-PLAN-2026-08.md` — W1 **done**; W2/W3/W4 open, all gated on the production deploy workflow
- Analytics & Entity SEO Plan: `de-website-3/ANALYTICS-SEO-PLAN.md`
- Course Schema & Carousel Plan: `de-website-3/COURSE-SCHEMA-PLAN.md`
- SEO Audit & Quick-Wins: `de-website-3/SEO-AUDIT.md`
- Long-Term SEO Plan: `de-website-3/SEO-LONGTERM-PLAN.md`

## Course Structured Data
- [Course schema implementation](course_schema_setup.md) — how `de_course_catalog()` + ACF repeater + custom location rule fit together. Sprint 1 shipped: DBA1/DBA2/DBA3 validated by Rich Results Test.

## SEO — Yoast & theme gotchas
- [Yoast SEO gotchas](yoast_seo_gotchas.md) — `wp_yoast_indexable` caches meta separately from `wp_postmeta`; theme's `header.php` used to emit duplicate OG tags (fixed 2026-04-13); utf8mb4 encoding on mysql CLI when piping from files.
