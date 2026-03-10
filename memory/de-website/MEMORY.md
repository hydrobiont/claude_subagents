# Project Memory — dataegret.com Website

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

**WARNING — Elementor publish resets page template**: Publishing from the Elementor editor on **both staging and production** resets `_wp_page_template` (to `default` on staging, to `elementor_canvas` on production). After every Elementor publish, immediately run:
```sql
UPDATE wp_postmeta SET meta_value='page-elementor-full.php' WHERE post_id=<ID> AND meta_key='_wp_page_template';
DELETE FROM wp_postmeta WHERE post_id=<ID> AND meta_key IN ('_elementor_element_cache', '_elementor_css');
```

### Affected post IDs (Elementor canvas service pages)

3295 (Courses), 4964, 5127, 5930, 6582, 6619, 6620, 7165 (Partners)

### Issue 2: Corrupted Elementor JSON after Python SQL escaping

**Root cause**: Using Python `val.replace("'", "\\'")` to escape SQL values is broken — double-escapes backslashes already in JSON (e.g. `\"`), producing invalid SQL/JSON.

**Fix**: Always use `mysqldump --no-create-info --where="..."` to export Elementor data, then convert `INSERT INTO` → `REPLACE INTO`. Never hand-escape JSON for SQL.

## Active Plans
- Analytics & Entity SEO Plan: `de-website-3/ANALYTICS-SEO-PLAN.md`
