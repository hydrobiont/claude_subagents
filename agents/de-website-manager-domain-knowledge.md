# Data Egret Website Manager — Domain knowledge

Seeded technical + strategic map for the `de-website-manager` agent, distilled from a full inspection of the `de-website-3` repo (theme code, infra/deploy docs, and the SEO/analytics/ads planning corpus) on 2026-06-09. The agent reads this file at the start of every run, alongside the project `MEMORY.md`.

The **SEEDED PROJECT KNOWLEDGE** below is the stable reference. The agent appends dated entries under the growth marker at the bottom as it learns. Verify any named file/function/slug/ID against current source before relying on it — the project moves.

---

## SEEDED PROJECT KNOWLEDGE

### Repo & directory map
- Working tree: `/Users/ik/work/de/website/de-website-3` (git; remote `dataegret/de-website-3`; branches `main` + `staging`). Only version-controlled app code = the custom theme `wp-content/themes/data-egret/`, plus `wp-content/mu-plugins/`, `scripts/`, `database/schema.sql`, and the planning docs. Third-party plugins and uploads are **not** in git.
- One level up `/Users/ik/work/de/website/`: working screenshots and the **un-versioned `serp-tracking/`** directory (dated SERP/GSC/GA4 CSVs).
- `google-ads/` — Python tooling + campaign CSVs (secrets in macOS Keychain, not on disk).

### Environments (full detail in `INFRASTRUCTURE.md`)
- **Dev**: Docker, `localhost:8080`, container `dataegret_wordpress`, DB `wordpress/wordpress@db:3306`, Apache/PHP7.4/MariaDB. phpMyAdmin on 8081 (dev profile only) + MailHog — local only, never deploy.
- **Staging**: `dev2.dataegret.com`, `ssh -p 50222 ik@svc.pgco.me`, WP root `/data/www/blog`, DB `blog / wordpressuser / wppasswordwp`, **WP-CLI present** (`/usr/local/bin/wp`), nginx + php7.4-fpm + OPcache. Noindex'd (`robots-config.php` Disallow:/). Has staging-only tweaks (Autoptimize, Elementor experiments — see `CHANGES-DB.md`).
- **Production**: `dataegret.com` (+ .eu/.de/.ru/.net aliases, all behind Cloudflare), `ssh -p 50202 ik@svc.pgco.me`, WP root `/data/www/blog`, same DB creds, **NO WP-CLI**, nginx + php7.4-fpm + OPcache. Cloudflare in front (purge for asset/markup changes).
- Env detection: mu-plugin `environment-config.php` uses `WP_ENVIRONMENT_TYPE` then hostname; **under WP-CLI it defaults to production** (bites on staging — pass host/path).
- SSH to either server needs a **YubiKey touch** → cannot run unattended.

### Deploy pipeline
- **Staging = automated**: push to branch `staging` → `.github/workflows/deploy-staging.yml`: server backup (theme tar + `wp db export`) → rsync `theme only` (`-av --delete-after --partial`, no `-z`) → chown www-data, 755/644 → `wp cache flush` + `wp elementor flush-css` → **restart php7.4-fpm (clears OPcache) + reload nginx**. Manual equivalent: `scripts/deploy.sh`.
- **Production = NOT automated yet** (spec in `PRODUCTION-DEPLOYMENT-PLAN.md`, unimplemented; would use a scoped `deploy-prod` user). Manual = rsync theme + php-fpm restart + nginx reload + Cloudflare purge; back up first. No WP-CLI ⇒ `wp` cache steps no-op on prod.
- Doc drift: README/CONTRIBUTING say `main`→staging but the live trigger is `staging`. Intent: `merge staging → main → push` for prod.
- DB scripts: `db-export.sh` (staging→local, utf8mb4), `db-import.sh` (local + search-replace host + flush), `db-export-schema.sh` (commits schema). `CHANGES-DB.md` lists DB-only changes to re-apply after a wipe.

### Theme code architecture (all PHP logic in `functions.php`; theme is custom, not a child)
Key functions / hooks (file:line as of inspection — re-grep to confirm):
- `theme_scripts` (`functions.php:22`, `wp_enqueue_scripts`) — enqueues `add79.css` (main hand-edited CSS, filemtime-busted), `ga-events.js` (filemtime-busted), big minified bundles (`main.min7`, `scripts.min12`, `add18`), and **conditional `course-cta.css/js`** when `is_singular('page')` AND slug ∈ `de_course_catalog()`.
- `de_get_datalayer_vars()` (`functions.php:186`) — computes `content_category` / `content_topic` / `page_type`. Pushed twice: raw `dataLayer.push` on `wp_head` **priority 1** (`:314`) and into each `gtag('config',…)` in `header.php`. Holds its **own** 7-slug `$service_slugs` list (`:207`) — separate from the locked list (see gotchas).
- `de_output_schema_json_ld()` (`functions.php:358`, `wp_head` **priority 5**) — the **only** JSON-LD emitter. Always emits Organization/ProfessionalService (`de_schema_org()`, `:691`, `@id .../#organization`). Then, gated by `post_name`: Service+OfferCatalog for `postgresql-support` (`:370`) and `postgresql-consulting` (`:394`); Course for slugs ∈ catalog (`:421`). FAQPage intentionally NOT in code (Elementor/AIOSEO own it).
- `de_course_catalog()` (`functions.php:435`) — single source of truth, keyed by page slug. 3 entries: `courses-postgresql-essentials-dba1`, `courses-postgresql-advanced-dba2`, `courses-postgresql-backups-replication-dba3`. Structural fields only (name, description, course_mode, language, workload_iso, credential, instructors). One edit auto-wires ACF fields + Course schema + course-cta assets + template locking.
- `de_course_schema($slug)` (`:473`) — merges catalog struct with ACF repeater `course_sessions` (dates/price/availability, edited in WP admin) → `Course` (+ `CourseInstance` + `Offer` per session). No sessions ⇒ bare Course (not rich-eligible). Custom ACF location rule `de_course_page` (`:551`) auto-shows the schedule fields on catalog-slug pages.
- `de_lock_elementor_full_template()` (`:680`, `save_post_page` **priority 20**) — for slugs ∈ `de_locked_full_template_slugs()` (`:662`): forces `_wp_page_template=page-elementor-full.php` and deletes `_elementor_element_cache` + `_elementor_css`. Self-heals the "Elementor publish resets template to canvas" bug — but only **on save**; direct DB writes need the manual recipe.
- Polylang: posts/cats/tags excluded from translation (`:95`); language tax filter stripped on author/archive (`:120`); ~35 UI strings registered (`:150`).
- `header.php` — GA4/GTM by language: en-GB GA4 host-switched `G-P3XRY2D4FB` (dev2) / `G-PLXB9VHN7B` (prod), GTM `GTM-5XTQZXB`; de-DE GA4 `G-0S38VWLP7K`, GTM `GTM-WFZ85BX`; ru-RU none. Exposes `window._dePageData`. **No OG/title/canonical here — Yoast owns them.**
- `page-elementor-full.php` — the locked template (get_header → the_content in `.elementor-wrapper` → get_footer). Backups to ignore: `page-team - save …`, `single - save- …`, `page-testing-blog.php`, `css/main.min7.css`.
- mu-plugins: `environment-config.php` (env detect + URL rewrite @priority 999 + admin notice), `elementor-environment-urls.php` (deeper Elementor/attachment URL rewrite), `redirects.php` (5 hardcoded 404→301), `robots-config.php` (staging blocks all; prod adds wp-admin/includes disallow).

### `ga-events.js` event catalogue (dual-dispatch: dataLayer + gtag)
`panel_open` (13 modals), `phone_click`, `email_click`, `form_submit` (CF7 success — IDs **159** Contact-EN / **1576** Join-Team-EN / **1399** Contact-DE; also Elementor Pro forms; also Pipedrive `postMessage` type 6 redirect), `article_read` (75% scroll on `body.single-post`), `service_read` (75% scroll when content_category=service), `page_not_found` (on `body.error404`). `form_submit` is the GA4 key event → imported into Google Ads as the conversion. `course-cta.js` builds the floating Register bar on course pages.

### GA4 custom dimensions (live, event-scoped)
cf7_status_message, contact_reason, discovered, formID, gtm_container, no_postgresql_installation, os_selected, postgresql_version, **content_category, content_topic, page_type**. Content taxonomy values: category = homepage/blog/service/landing/page/hub/about/404/search; topic = performance/replication/backup/data-analytics/migration/monitoring/connection-pooling/tools/other; page_type = landing/article/archive/404.

### Plan-doc index (in `de-website-3/`) — pull the right doc, don't reinvent
| Doc | Covers | Status |
|---|---|---|
| `INFRASTRUCTURE.md` | env specs, prod↔staging↔local DB sync recipes | reference |
| `ENVIRONMENT-MANAGEMENT.md`, `STAGING-ENVIRONMENT.md`, `PRODUCTION-SETUP.md` | env config, plugin versions, hardening | reference |
| `PRODUCTION-DEPLOYMENT-PLAN.md` | the unimplemented prod CI pipeline + manual checklist | planned |
| `CHANGES-DB.md` | DB-only changes not in code (re-apply after wipe) | reference |
| `SECURITY.md`, `SECURITY-REVIEW.md` | secrets posture ("safe to commit") | reference |
| `ANALYTICS-SEO-PLAN.md` | 5-phase analytics plan + entity-SEO model | Phase 1 shipped; rest planned |
| `SEO-AUDIT.md` | the diagnosis + Sprint-1 quick wins | Sprint 1 shipped 2026-04-13 |
| `SEO-LONGTERM-PLAN.md` | Sprints A–F roadmap, CTR/clicks targets | planned |
| `GA4-ANALYSIS-2026-05.md` | traffic teardown (low & declining; funnel gaps) | reference |
| `COURSE-SCHEMA-PLAN.md` | Course JSON-LD + hub carousel, 4 sprints | Sprint 1 (DBA1/2/3) shipped & validated |
| `DBA-COURSES-CONVERSION.md` | 9 conversion gaps on course pages | planned |
| `DBA-COURSES-PAID-SEARCH.md`, `google-ads/SETUP-GUIDE.md` | the 3 Ads campaigns | built, PAUSED |
| `LANDING-PAGES-PROPOSAL.md` (V1) | 4 blog-overlap landing pages (DR/Perf/Migration/Remote-DBA) | planned |
| `LANDING-PAGES-PROPOSAL-V2.md` | buyer-intent reframe, no-pricing-on-service | **parked** |
| `SUPPORT-SERVICES-PLAN.md` | support/consulting findability + €2,500/mo pricing + Calendar booking | planned (support-page schema shipped) |
| `serp-tracking/INSTRUCTIONS.md` | the SERP-tracking method/cadence | recurring |

### Status ledger (snapshot 2026-06-09)
- **Shipped**: SEO Sprint-1 quick wins (OG/title dedup, H1 fixes on 6 course pages, 3 meta descriptions, typo); Course schema DBA1/2/3 (Rich-Results validated); content-taxonomy dimensions; the ga-events.js event set; `/postgresql-support/` 3-tier Service OfferCatalog JSON-LD + link colours; SERP baseline (2 runs).
- **Built but not launched**: Google Ads campaigns 1–3 (PAUSED; Paid traffic = 0).
- **Blocked**: Google Ads API Basic Access (developer-token approval pending) — use CSV/Editor import meanwhile.
- **Planned**: Course schema Sprints 2 (Dev courses) & 3 (hub ItemList carousel); DBA conversion fixes (testimonials, FAQ, hub €850 price, sticky CTA, above-fold form); remaining H1 fixes (5 pages) + image alts + 687-not-indexed cleanup; title/meta rewrites; blog→service internal linking (`[de_service_box]`); thin-page expansion; landing pages V1; support pricing + `/postgresql/services/` hub + Calendar booking + nav refurb + 4th Ads campaign.
- **Open technical**: DBA3 page 0.7s dwell / 80% bounce (needs Lighthouse); GA4 bot/"(not set)" filtering.

### Google Ads specifics
Account `159-128-5976` via MCC `665-380-3633`. Campaign 1 *DBA Courses–Search* (€15/day, 4 ad groups: DBA1/2/3 + Brand Defence, 25 phrase keywords, 15 negatives). Campaign 2 *Courses Hub–Search* (€0→€10, EN + DE ad groups). Campaign 3 *Course Remarketing–Display* (€5/day, "Course visitors no registration" audience). 12 headlines/4 descriptions per DBA RSA; 6 sitelinks/9 callouts/2 snippets. GA4↔Ads linked; `form_submit` is the conversion. Python path (`create_campaigns.py`, OAuth via Keychain) builds everything PAUSED, defaults to the test account; gated on dev-token. **Enable Campaign 1 first** when launching (per GA4 analysis), only with user go-ahead.

### SERP tracking
12 commercial queries (postgresql consulting/support/consultant/dba/performance/managed/experts + postgres variants). GSC = ground truth (9 geos). WebSearch spot-checks US-only (EU GDPR consent walls). GA4 organic via analytics MCP (property 356651240, Organic segment). Dated CSVs, never overwrite, every 4–6 weeks. Baseline: dataegret.com NOT in US top-10 for any commercial query; recurring competitors postgres.ai, cybertec, percona, EDB, pgexperts, crunchydata, stormatics, jusdb, pythian.

### Open decisions (surface to user; don't silently pick)
1. **AIOSEO is active** (auto-generates FAQ schema, commit `0e2b2e4`) despite `SEO-AUDIT.md` calling it dormant → two SEO plugins emit meta. Resolve ownership before more schema work.
2. **Pricing on service pages**: `SUPPORT-SERVICES-PLAN.md` (show €2,500/mo) vs `LANDING-PAGES-PROPOSAL-V2.md` (no pricing). Conflict.
3. ru-RU GA4/GTM IDs in `ANALYTICS-SEO-PLAN.md` vs "removed" in memory → trust live `header.php` (no ru-RU branch).

### Tool-routing playbook
- GA4 numbers → `analytics` MCP (`ToolSearch` then `mcp__analytics__run_report` etc.).
- Live Elementor editor / Yoast / WP-admin clicks / page screenshots → delegate to **`browser-operator`** (precise URL + change + verification).
- Elementor `_elementor_data` bulk/surgical fix → SQL on staging + the cache trifecta (prefer mysqldump `--where` → REPLACE, or `UPDATE … UNHEX`).
- Staging WP ops → `wp` over SSH (or `dataegret-staging` MCP if loaded).
- Blog posts / runbooks / doc-quality copy → `technical-writer` skill; client PDFs/HTML → `client-report-builder`.
- Tech/library/format choice → `architecture-advisor`.
- Schema validation → Google Rich Results Test (`curl` the page, or browser-operator).

### Gotchas (high-injury)
- Elementor cache trifecta on any DB-level page/template change (template + `_elementor_element_cache` + `_elementor_css`), else stale HTML.
- Never hand-escape JSON for SQL (double-escapes `\"`); use mysqldump/REPLACE or `UNHEX`.
- Two divergent slug lists (`de_locked_full_template_slugs()` vs `$service_slugs` in `de_get_datalayer_vars()`) — update both.
- Unclosed `<tag>` in widget text cascades into nested/non-full-width sections (balance tags).
- Don't emit OG/title/canonical in theme (Yoast owns them); FAQPage schema lives in Elementor/AIOSEO, not PHP.
- WP-CLI defaults to *production* env when host unset; prod has no WP-CLI at all.
- Deploy syncs theme only; never push docker-compose/phpMyAdmin/MailHog.
- `deploy.sh` env-loading breaks on `.env` values containing spaces/quotes.

---

<!-- entries below; newest on top -->

### Elementor is a first-class constraint in every infra/deployment decision (user directive 2026-06-10)
When evaluating hosting/deploy/runtime changes, explicitly enumerate Elementor's surfaces before concluding: (1) page content is DB-resident JSON (`_elementor_data`) — never deployed by code pipelines; (2) runtime-regenerated CSS cache lives under `wp-content/uploads/elementor/css/` + `_elementor_css`/`_elementor_element_cache` postmeta — mutable state that breaks "immutable image" assumptions and needs flushing after PHP/plugin/env changes; (3) Elementor Pro is licence-bound to domains — migrations and staging URL changes touch licensing; (4) it is the most PHP-version-sensitive plugin in the stack — any PHP upgrade rehearsal must exercise the Elementor *editor*, not just the front-end.

### GSC remediation Phase 1 shipped to staging (2026-06-10)
Commits `dbbbf23` (recovered the uncommitted April course-sprint working tree — see hazard below), `7369893` (redirects map + popup CPT non-public + CI ships mu-plugins), `f06acd1` (rewrite fix). Verified on dev2: all 301s hit real targets, `/popup/*` junk → 410, popup-sitemap.xml dropped from Yoast index, modals + Course schema intact. Deployment schema decided: **B — CI-only SSH with scoped deploy users** (no manual SSH for deploys; org plan is `team` so a gated `production` environment is available). Phase 2 pending: provision `deploy-stg`/`deploy-prod` users (one YubiKey session), fresh ed25519 keys → GitHub Secrets (replace personal `ik` key), `deploy-production.yml` (push to main + workflow_dispatch, environment approval), bump `actions/checkout` & `ssh-agent` (GitHub forces Node 24 on 2026-06-16). Phase 3: prod deploy + GSC Validate-fix.

### WP gotcha — CPT made non-public still 301s to home until rewrite rules are flushed
Setting `publicly_queryable=false` on a CPT does NOT remove its cached rewrite rules (`rewrite_rules` option). Requests to `/cpt/<slug>/` still match the stale rule, the unregistered query var resolves the request to the homepage, and `redirect_canonical` 301s it to `/` — so `is_404()`-based redirect handlers never fire. Fix: also set `rewrite=false` + `query_var=false` in the `register_post_type_args` filter (else a flush regenerates the rules), then do an **option-guarded one-time `flush_rewrite_rules()`** in code (`init` prio 99, version-string option). Code-level flush is mandatory for this project: production has no WP-CLI.

### Repo hazard — scripts/deploy.sh ships the working tree, so servers can be ahead of git
The April 2026 course-schema sprint lived only as uncommitted working-tree changes; servers got it via `scripts/deploy.sh` (rsyncs local tree), while the `staging` branch lagged. Any CI push at that point would have rsync-`--delete`d the un-committed work off the server. **Before pushing to `staging`, always `git status` the theme and commit working-tree drift first.** mu-plugins now deploy via CI too (rsync without `--delete`, so server-only files survive).

### GSC indexing baseline — dataegret.com (2026-06-09)
GSC property is a **domain property** `sc-domain:dataegret.com` (the only one), so it aggregates **all subdomains incl. staging `dev2`**. 287 indexed / 507 not-indexed (down from ~687 in Apr — improving). "Why not indexed": Crawled-not-indexed **305** (thin tag/category/author archives, `/feed/` variants, old posts — Google quality call, long-standing since 2023); Excluded-by-noindex **85** (feeds + `/YYYY/MM/` date archives + author archives — WordPress/Yoast default, working as designed, no action); **Not found 404 = 50 (most actionable)**; Blocked-by-robots **27** (9/10 are `dev2` staging URLs — correctly blocked by `robots-config.php`, just noisy in the domain property; first detected 2026-03-07); redirect 15; alt-canonical 6; other-4xx 2; discovered-not-indexed 11; dup-canonical 5+1. Enhancements all valid, **0 errors**: Breadcrumbs 58, FAQ 4, Profile 1 (Course schema DBA1/2/3 not yet surfaced as its own enhancement row — monitor). The Jun 1 + Jun 9 "new reasons" email notifications are driven by the 404 bucket (popup slugs re-crawled) plus new `dev2` sitemap URLs. Screenshots saved under `/Users/ik/work/de/website/0[1-7]-*.png`.

### Production 404s to remediate (confirmed via curl 2026-06-09 — all 404, no existing redirect)
`/popup/<slug>/` modal-CPT URLs (≥6 visible, mostly Russian slugs: `консультирование-postgresql`, `политика-конфиденциальности`, `marketing-assistant`, `менеджер-по-продажам`, autovacuum-workers…) — these map to the 13 `panel_open` modals in `ga-events.js`; the popup CPT is exposing public standalone URLs that 404. Also `/ultimate-plan/` (matches the `ultimate-plan` modal), `/ru/` + `/en/` (Polylang language-root artifacts; ru-RU content was removed), and `/news-blog/postgresql-resourses/` (the pre-rename **typo** slug — the corrected `postgresql-resources` returns 200). `redirects.php` currently holds only 5 hardcoded 404→301s and covers none of these. Fix options: add 301s in `redirects.php`; set the popup CPT `public=false`/`publicly_queryable=false` + exclude from sitemap so it stops minting indexable URLs; 301 the typo slug to the corrected one. The `/popup/postgresql-consulting/` overlay URL was already flagged polluting SERPs in the SERP-tracking baseline.
