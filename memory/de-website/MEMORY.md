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
- Key plugins: ACF Pro, Contact Form 7, Polylang, All-in-One SEO, Yoast SEO, Real Cookie Banner, Custom Post Type UI

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

Staging vs production switch for en-GB in header.php:
```php
$ga4_en_id = (strpos($_SERVER['HTTP_HOST'], 'dev2.dataegret.com') !== false) ? 'G-P3XRY2D4FB' : 'G-PLXB9VHN7B';
```

## Custom Event Tracking
`wp-content/themes/data-egret/js/ga-events.js` — custom JS tracking:
- `panel_open` — modal/popup opens (Contact Form, Training, Consulting, etc.)
- `phone_click` — phone link clicks
- `email_click` — email link clicks
- `form_submit` — CF7 success (form IDs: 159=Contact EN, 1576=Join Team EN, 1399=Contact DE)
- `page_not_found` — 404 detection

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
- Production SSH: `ssh -p 50202 ik@svc.pgco.me` (hardware YubiKey required — touch to auth)
- Staging SSH: `ssh -p 50222 ik@svc.pgco.me`
- WP root (both servers): `/data/www/blog`
- DB credentials: `mysql -u wordpressuser -pwppasswordwp blog`
- WP-CLI: staging only (`/usr/local/bin/wp`), NOT installed on production
- Full infra docs: `de-website-3/INFRASTRUCTURE.md`

## Elementor Canvas Pages — Known Issues & Fixes

### Issue 1: False/duplicate Elementor nav on service pages

**Root cause A**: Pages used `elementor_canvas` page template on production, which bypasses `get_header()` entirely. All navigation came from an Elementor-built header section inside `_elementor_data`. Staging used `page-elementor-full.php` (calls theme `get_header()` + `get_footer()`).

**Fix A**: `UPDATE wp_postmeta SET meta_value='page-elementor-full.php' WHERE post_id IN (...) AND meta_key='_wp_page_template';`

**Root cause B**: After fixing `_elementor_data` (removing nav widgets) and switching the page template, Elementor was still serving old rendered HTML from its server-side cache stored in `_elementor_element_cache` postmeta. The DB data was clean but the cache was stale.

**Fix B**: `DELETE FROM wp_postmeta WHERE post_id IN (...) AND meta_key='_elementor_element_cache';`

**Always do all three** when modifying Elementor page data or templates:

1. Update `_wp_page_template`
2. Delete `_elementor_element_cache`
3. Delete `_elementor_css`

**~~WARNING — Elementor publish resets page template~~ — RESOLVED 2026-04-13**: Previously, publishing from the Elementor editor reset `_wp_page_template` to `elementor_canvas` (production) or `default` (staging), requiring manual SQL fixes. Now handled by the `de_lock_elementor_full_template` hook in `functions.php` (`save_post_page`, priority 20). The hook re-enforces `page-elementor-full.php` on every save for any slug listed in `de_locked_full_template_slugs()` and clears `_elementor_element_cache` / `_elementor_css`. Adding a course to `de_course_catalog()` automatically extends this protection.

If a NEW page should also be locked, add its slug to `de_locked_full_template_slugs()`. To unlock a page, remove its slug.

**Legacy manual recipe (still works if the hook is disabled or for one-offs):**
```sql
UPDATE wp_postmeta SET meta_value='page-elementor-full.php' WHERE post_id=<ID> AND meta_key='_wp_page_template';
DELETE FROM wp_postmeta WHERE post_id=<ID> AND meta_key IN ('_elementor_element_cache', '_elementor_css');
```

### Affected post IDs (Elementor canvas service pages)

3295 (Courses), 4964, 5127, 5930, 6582, 6619, 6620, 7165 (Partners)

### Issue 2: Corrupted Elementor JSON after Python SQL escaping

**Root cause**: Using Python `val.replace("'", "\\'")` to escape SQL values is broken — double-escapes backslashes already in JSON (e.g. `\"`), producing invalid SQL/JSON.

**Fix**: Always use `mysqldump --no-create-info --where="..."` to export Elementor data, then convert `INSERT INTO` → `REPLACE INTO`. Never hand-escape JSON for SQL. The most robust write-back is `UPDATE ... SET meta_value = UNHEX('<hex>')` — zero escaping concerns.

### Issue 3: Unclosed HTML tags in widgets cause full-width sections to render nested

**Symptom**: Top-level Elementor sections appear nested inside an earlier section in the DOM; backgrounds don't stretch edge-to-edge.

**Root cause** (NOT structural data corruption): Widget text fields contain malformed HTML (unclosed `<div>`, truncated `<a href="..." rel="..."` without `>`). Browser swallows subsequent HTML into the open element, cascading the misparse.

**Key diagnostic**: Parse `_elementor_data`, walk all widget text fields, count `<tag>` vs `</tag>` balance. Full detection + repair recipe in [elementor_unclosed_html_tags.md](elementor_unclosed_html_tags.md).

## Collaboration Preferences
- [No co-author in commits](feedback_no_coauthor.md) — never add Co-Authored-By Claude line

## Deployment Schema (decided 2026-06-10)
**CI-only SSH, scoped keys** — no manual SSH for deploys. Staging: `deploy-staging.yml` now also ships `wp-content/mu-plugins/` (rsync **without** `--delete`; backup + perms included). Pending Phase 2: scoped `deploy-stg`/`deploy-prod` users replace the personal `ik` key in GitHub Secrets; new `deploy-production.yml` gated by a `production` GitHub environment (org plan `team` supports required reviewers). Bump `actions/checkout@v4`/`ssh-agent@v0.9.0` before 2026-06-16 (Node 24 forced).
**Hazard**: `scripts/deploy.sh` deploys the *working tree* — servers can be ahead of git. Always commit theme drift before pushing `staging` (the April course sprint was recovered into commit `dbbbf23` this way).

## Popup CPT & dead-URL redirects (2026-06-10)
- `mu-plugins/popup-cpt-visibility.php`: popup CPT is non-public (`publicly_queryable=false`, `rewrite=false`, `query_var=false` + option-guarded one-time `flush_rewrite_rules()`). Footer modals unaffected (rendered inline via WP_Query); Yoast dropped `popup-sitemap.xml` automatically. **Gotcha**: without `rewrite=false`+flush, stale rewrite rules make `/popup/<slug>/` canonical-301 to home and `is_404()` handlers never fire. Code-level flush is mandatory — production has no WP-CLI.
- `mu-plugins/redirects.php`: rawurldecodes paths (Cyrillic slugs); 301 map for dead popups / `/ultimate-plan/` / `/ru/` / `/en/` / `resourses` typo; **410 catch-all** for any other `/popup/*`.
- GSC baseline 2026-06: 287 indexed / 507 not-indexed; the Jun 1+9 notifications were popup-404s + dev2 sitemap noise (domain property `sc-domain:dataegret.com` covers subdomains). Full detail in `~/.claude/agents/de-website-manager-domain-knowledge.md`.

## Active Plans
- Analytics & Entity SEO Plan: `de-website-3/ANALYTICS-SEO-PLAN.md`
- Course Schema & Carousel Plan: `de-website-3/COURSE-SCHEMA-PLAN.md`
- SEO Audit & Quick-Wins: `de-website-3/SEO-AUDIT.md`
- Long-Term SEO Plan: `de-website-3/SEO-LONGTERM-PLAN.md`

## Course Structured Data
- [Course schema implementation](course_schema_setup.md) — how `de_course_catalog()` + ACF repeater + custom location rule fit together. Sprint 1 shipped: DBA1/DBA2/DBA3 validated by Rich Results Test.

## SEO — Yoast & theme gotchas
- [Yoast SEO gotchas](yoast_seo_gotchas.md) — `wp_yoast_indexable` caches meta separately from `wp_postmeta`; theme's `header.php` used to emit duplicate OG tags (fixed 2026-04-13); utf8mb4 encoding on mysql CLI when piping from files.
