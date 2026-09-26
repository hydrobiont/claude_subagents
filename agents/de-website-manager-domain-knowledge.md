# Data Egret Website Manager — Domain knowledge

## 2026-08-14 — STANDING RULE (user directive): Stripe = ONE designated sandbox only

The user opened a single Stripe **Sandbox** (account uses Google Workspace SSO;
no standalone credentials exist) for the course-booking integration.
**All Stripe work — configuration, keys, webhooks, test payments — happens
ONLY inside that one sandbox. Never live mode, never another sandbox, never
account-level settings.** Verify the sandbox context before ANY Stripe action;
if the dashboard is not in that sandbox, stop and report.
Sandbox identity + key storage (1Password dataegretgmbh vault item
"Stripe SANDBOX … — course booking PoC"; macOS Keychain services
`stripe-sandbox-secret` / `stripe-sandbox-publishable`) are pinned in
browser-operator's domain knowledge from its first-entry report.
Off-prod Odoo builds receive sandbox keys only (the re-arm runbook asserts the
`sk_test_` prefix and refuses anything else). Live keys enter Odoo production
only at the user-gated go-live step, entered by the user.

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
- **Staging**: `dev2.dataegret.com`, `ssh -p 50222 ik@svc2.pgco.me`, WP root `/data/www/blog`, DB `blog / wordpressuser / wppasswordwp`, **WP-CLI present** (`/usr/local/bin/wp`), nginx + php7.4-fpm + OPcache. Noindex'd (`robots-config.php` Disallow:/). Has staging-only tweaks (Autoptimize, Elementor experiments — see `CHANGES-DB.md`).
- **Production**: `dataegret.com` (+ .eu/.de/.ru/.net aliases, all behind Cloudflare), `ssh -p 50202 ik@svc2.pgco.me`, WP root `/data/www/blog`, same DB creds, **NO WP-CLI**, nginx + php7.4-fpm + OPcache. Cloudflare in front (purge for asset/markup changes).
- Env detection: mu-plugin `environment-config.php` uses `WP_ENVIRONMENT_TYPE` then hostname; **under WP-CLI it defaults to production** (bites on staging — pass host/path).
- SSH: **staging runs unattended, production needs the YubiKey** (re-measured 2026-08-10 — see the non-interactive-SSH section below for the exact stderr noise to ignore and the working invocation). Host is **`svc2.pgco.me`**, not `svc.pgco.me`.

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

### Booking bridge — the three traps the 2026-08-15 review turned up (bridge 0.2.0)
**(1) A slug that ends in its own short code breaks substring fixtures.** The L1 runner built its BOOK-05 negative case as `${bad/dba1/nonexistent-course}`; once the fixture carried the canonical `courses-postgresql-essentials-dba1`, that rewrote the slug's *tail* into `courses-postgresql-essentials-nonexistent-course` — still a 422, so the test passed while asserting something nobody intended. Negative fixtures must replace the whole value (the runner's `fixture()` now takes `course_code` as a parameter). **(2) A duplicated intake path is a latent lie, not a fallback.** The Elementor `elementor_pro/forms/new_record` handler duplicated the REST route's reject-vs-retry logic, drifted, and ended up queueing 401/422 rejections while telling the visitor "your seat is recorded" — for a form that never existed. Removed rather than repaired; if one is ever needed again, wire it to the shared helpers. **(3) `Retry-After` is a floor, never a replacement.** 429 is now retryable on the existing queue ladder (1 m → 5 m → 30 m → 1 h → 2 h), but the header is applied as `max(ladder, retry_after)` and capped at 1 h — honoring it as a *replacement* would let a server answering "retry in 30 s" burn all five attempts in two minutes and give up. Cross-system gotcha worth remembering: the spec's 503-vs-429 rule is keyed on the **deployed** bridge version, which is invisible from Odoo — `wp de-booking status` prints it as its first line.

### Committed test reports must never carry a portal access token (2026-08-15)
v1.1 makes `payment_url` a tokenized customer-portal order page (`/my/orders/<id>?access_token=…`) — a forwardable, **payable** link by design. `tests/booking/reports/` is version-controlled, so any runner assertion that quotes a `payment_url` must strip the query string (`${PAY_URL%%\?*}`) before writing evidence. Same reflex applies to anything else that captures that URL: screenshots, logs, handoff notes. The rule is now in spec D2.7.

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

### ⚠ Cloudflare WAF — a host-scoped OWASP skip protects the Odoo ERP; DO NOT remove or reorder it (2026-08-04)
The `dataegret.com` zone (`d06ff7e352dbfd95b4944815d755f6fb`, **Pro Website**) fronts more than the website: **`odoo.dataegret.com` is an orange-cloud record pointing at the company's Odoo ERP on odoo.sh**, so this zone's WAF sits in front of a production ERP and its customer portal.

On 2026-08-04 the **OWASP Core Ruleset** (running at Cloudflare defaults — score threshold 40, no overrides) was found blocking ordinary ERP traffic: the Odoo 2FA page `GET /web/login/totp` (score exactly 40 — locked a colleague out mid-invite), `POST /report/download` (45), `POST /website/form/helpdesk.ticket` (89), and any POST body containing SQL (fatal for a PostgreSQL consultancy whose customers paste queries into tickets).

**Live mitigation — treat as load-bearing.** Managed-phase entrypoint ruleset `1d994ae8beb241c4bd895e0b1684f420`, rule **1** = `skip` → `rulesets: ["4814384a9e5d4991b9815dcfc25d2f1f"]` (OWASP Core) where `http.host eq "odoo.dataegret.com"`. Two hazards: the skip **must stay ahead of the two `execute` rules** (an exception placed after them skips nothing), and it must stay **host-scoped** — widening the expression would strip OWASP from the website too. The Cloudflare Managed Ruleset `efb7b8c949ac4650a09736fc376e9aee` stays on everywhere and still catches `/.git/*` scanners plus query-string SQLi on the Odoo host. Verified A/B after the change: identical SQL-body POST → `dataegret.com` **403 blocked**, `odoo.dataegret.com` reaches origin. **The apex's own protection is unchanged.**

If you ever rebuild, reorder or migrate this zone's WAF rules for website reasons, re-assert that skip rule first or you re-break the ERP — with no symptom on the website at all.

**Debugging trap worth knowing zone-wide:** a Cloudflare block page interpolates the **zone apex**, so a block on any subdomain still reads *"You are unable to access dataegret.com"*. Do not assume the apex was the target. Attribute by the response `server:` header and by `firewallEventsAdaptive` (`clientRequestHTTPHost`). Security Events retention on Pro is **24 hours** — grab evidence the same day; only OWASP events carry `score_total`/`score_rules`.

### ⚠ In-scope hosts are exactly two — never route around a connectivity block (user directive 2026-08-10)
This project touches **only** staging `svc2.pgco.me:50222` (server hostname `dev2`) and production `svc2.pgco.me:50202` (server hostname `blog`). That host is a **gateway that port-forwards to two separate servers**, which is why one IP serves both and why a bare-IP `https://<ip>/` returns 502 rather than the site.

**⚠ The gateway is `svc2.pgco.me` (5.9.102.135) — corrected 2026-08-10, verified live.** The old `svc.pgco.me` (148.251.134.145) still resolves but **no longer serves these ports**; `:443` on it answers, `:50222`/`:50202` do not. `de-website-3/CLAUDE.md`, `INFRASTRUCTURE.md` and `MEMORY.md` all still say `svc.pgco.me` and are **stale** — prefer `svc2` and treat the repo docs as wrong here until they are fixed. Measured the same day: `svc2:50222` OPEN, `svc2:50202` OPEN, `svc:50222` FAILED, `svc:50202` FAILED.

**`ap3.pgco.me` — the `mbt` alias in `~/.ssh/config` — is NOT part of this project.** Do not connect to it, tunnel through it, ProxyJump via it, or treat it as a bastion. On 2026-08-10 it was assumed to be one purely because it was the only reachable host in the user's SSH config; that assumption was wrong and explicitly rejected. **Nothing outside the two hosts above is in scope without asking first.**

**Non-interactive SSH: staging YES, production NO (re-measured 2026-08-10 — supersedes the blanket "impossible").** `~/.ssh/config` has a `Host *` block setting `PKCS11Provider /opt/homebrew/lib/opensc-pkcs11.so` with **`IdentityAgent none`**, so every invocation *tries* the YubiKey PIV path first and fails noisily without an askpass binary. What happens next differs by host:

- **Staging (`:50222`) works unattended.** The PKCS11 attempt fails, then auth **falls through to a working key** and the command runs. Expect this noise on stderr and ignore it — it is not an error:
  `ssh_askpass: exec(/opt/homebrew/Cellar/openssh/10.3p1/libexec/ssh-askpass): No such file or directory` / `login failed` / `pkcs11_get_key failed` / `sign_and_send_pubkey: signing failed for RSA "Authentication key": agent refused operation`
  Then it prints real output. Send SQL via `ssh ... 'mysql -u wordpressuser -pwppasswordwp blog -t' <<'SQL'` and add `2>/dev/null` to suppress the noise. Requires `dangerouslyDisableSandbox: true` (non-standard port).
- **Production (`:50202`) does NOT work unattended.** The same PKCS11 failures repeat until the server cuts the connection: `Received disconnect ... Too many authentication failures`. The YubiKey PIN genuinely gates production, and there is no askpass binary installed to prompt with.

Do **not** try to reach production by hopping from staging — a ProxyJump/jump-host hop is exactly what the user's standing directive forbids. Ask instead.

**When the SSH ports are unreachable:** symptom is `connect to ... port 50222: Network is unreachable` — `ENETUNREACH`, uniform across ports 22/50202/50222, while `:443` on the same IP answers normally.

**Check the hostname FIRST — on 2026-08-10 this exact signature was just the stale `svc.pgco.me`, not an allowlist.** Two hours went into sandbox theories and hunting for local port-forwards before the user supplied `svc2`. Diagnostic order: (1) `nc -z -w8 svc2.pgco.me 50222` — if OPEN the host was simply wrong; (2) only if `svc2` also fails, suspect a **source-IP allowlist** (user's public IP changed; nginx allowlists Cloudflare, UFW inactive per `INFRASTRUCTURE.md`). Then **report it and ask how access is normally granted.** Do not look for another route in.

**A sandbox red herring to skip:** the Bash tool's sandbox blocks non-standard ports *and* silences `lsof -iTCP` (returns only a header, looking like "no listeners"). Re-run with `dangerouslyDisableSandbox: true` before concluding anything about listeners or tunnels — but note that in this incident the sandbox was **not** the cause; unsandboxed failed identically.

**Verify which box you are on before any destructive DB work.** The staging/production split is one digit in a port number on a shared gateway, so assert on the server's own `hostname -s` (`dev2` vs `blog`) rather than trusting connection parameters.

### WordPress.com migration program state + deploy-pipeline repairs (2026-08-10)

**WordPress.com account:** Business plan site is **`dataegret.wpcomstaging.com`** (renamed from `dataegret.wordpress.com` by the Atomic transfer on 2026-08-10; old name 301s). Hosting features active; **data center EU West (Amsterdam)** (`geo_affinity=ams`); **PHP 8.4, WordPress 7.0.3** (no PHP 7.4 offered — 8.3/8.4 only); unlaunched = Coming-Soon, `robots.txt` serves `Disallow: /`. SFTP enabled: `sftp.wp.com:22`, user `dataegret.wordpress.com` (password shown once in UI — reset it to view again; never store it). SSH enabled but keyless — attaching a key is an account-level, user-policy decision (YubiKey project owns key policy). Staging site: **`staging-7eb1-dataegret.wpcomstaging.com`** (built 2026-08-10; a "Sync" button on the production overview appears once it exists — bidirectional, treat "push to production" as forbidden). GitHub Deployments: WordPress.com GitHub App **installed** on the `dataegret` org, scoped to the single repo `de-website-3` (installation id 152735027); connect-repo form verified: branches `main`/`staging` selectable, destination dir free-text (default `/`), Automated-deployments checkbox, Simple/Advanced radio. **Advanced mode = your own GitHub Actions workflow must upload an artifact with a required name; the form's "Workflow check" validates: valid YAML, triggered on push, artifact name.** Do NOT reuse `deploy-staging.yml` (that's the dev2 rsync pipeline — it fails the artifact check); author a dedicated `deploy-wpcom-*.yml`. **Staging site connected and deploying** (2026-08-10): repo → branch `staging`, destination `/`, Advanced mode, auto-deploy ON, workflow `.github/workflows/deploy-wpcom-staging.yml` (uploads artifact named `wpcom` containing ONLY theme+mu-plugins; passed all three wpcom checks). First deployment `82f8cc8` verified: theme assets 200, repo docs 404, SAFE-02 zeros. Every push to `staging` now deploys BOTH dev2 (rsync) and wpcom staging (artifact) — two green workflows on one push. Production site connection deferred to `main` (manual) at cutover; per docs one repo→one destination per connection, so use Advanced mode, destination `/`, artifact assembling `wp-content/themes/data-egret/` + `wp-content/mu-plugins/`; deployments **merge, never delete** — stale-file check required (spec SMK-05). Plan is billed **monthly €60** — annual €300/yr pending user decision. The original signup site `ik734f65b41b03f-tilhr.wordpress.com` had a **WordPress.com-run "Incoming Migration" request** that locked its entire hosting dashboard (`/hosting-config` 404s, everything redirects to `/migration-overview`, no cancel button); plan was refunded off it and the site queued for user-click deletion — deleting the site extinguishes the stuck request. **Lesson: never submit the WordPress.com migration-request flow for this project** — it locks the dashboard for days and expects production credentials. The PoC is manual assembly from dev2 per `wpcom-migration` plan; test contract lives in the wpcom-test-spec artifact (SAFE/SMK/DBI/FULL suites).

**Staging deploy pipeline repaired the same day** (was broken since the gateway move; last green run 2026-06-10): GitHub secrets `SSH_HOST`→`svc2.pgco.me`, `SSH_PORT`→`50222`; `/home/github-deploy` was owned `root:root` so the CI user couldn't `mkdir ~/backups` — chowned to `github-deploy`. CI auths as dedicated `github-deploy` user (scoped NOPASSWD sudoers: rsync/chown/chmod/find/systemctl), NOT the personal `ik` key.

**Analytics gate (Phase 2a/2b) shipped in `1af34fa`:** `de_analytics_mode()` + `de_production_hosts()` allowlist in `environment-config.php`; header.php fail-closed (`'none'` if helper missing); robots fallback flipped to staging. Verified live: dev2 serves 0 production GA4 IDs, staging `G-P3XRY2D4FB` intact, `Disallow: /`.

**Gotcha class discovered — Complianz resurrects comment-wrapped scripts:** its output filter rewrites `<script>` tags **inside HTML comments** into consent-gated `text/plain` tags, so "commented-out" tracking snippets in `ihaf_insert_header` still emit their IDs into served HTML on every host. Removed on staging (rollback `/home/ik/ihaf_insert_header.bak-20260810`); **production still carries the block** — remove at cutover. When auditing tracking, grep the *rendered page*, never trust source comments.

**Pre-existing quirk, unfixed:** `/startseite/` (German homepage) renders with `en-GB` analytics on dev2 — Polylang language detection is off for it on staging. Off-production it's silenced by the gate; flagged for someday.
