# Browser Operator — Domain knowledge

Persistent notes accumulated by the `browser-operator` agent across invocations. The agent reads this file at the start of every run and appends entries when it learns something durable about the domain — e.g. quirks of specific admin panels, selectors that change over time, sites that fight Playwright in known ways, authentication patterns that persist via the dedicated profile, etc.

See the agent definition (`browser-operator.md`) for the rules on what belongs here vs not.

<!-- entries below; newest on top -->

### Odoo Project ▸ Projects — DBA now visible; action IDs and filter history (Jun 2026)

`/odoo/project` (action-202 as of 2026-06-29; previously also action-203 depending on session) carries domain `[["is_internal_project","=",false],["helpdesk_team","=",false],["is_template","=",false]]`. Until 2026-06-29 this excluded DBA (helpdesk_team=17) and Customer Care (team 1); only Field Service + Happy Numbers [Support] appeared (pager 1-2/2). After a server-side fix applied by 2026-06-29, the pager shows **1-4/4** and all four projects appear: **Customer Care, DBA (45 Tasks), Field Service, Happy Numbers [Support]** — meaning the action domain on the server was updated to no longer include the `helpdesk_team=false` condition (or DBA's helpdesk_team link was cleared). Action-203 (`/odoo/action-203`) is a task kanban grouped by stage (To Do / In Progress / Done / Cancelled), not a projects list. To read the live action domain use `window.owl.App.apps` → `app.env.services.action.currentController.action.domain`.

### Odoo All Tasks (action-215) — domain, default filter, and task distribution (Jun 2026)

`/odoo/all-tasks` (action-215) has domain `[["has_template_ancestor","=",false],["has_project_template","=",false]]` with context `{"search_default_open_tasks":1}` — the "Open" filter is active by default. With that filter the view shows **40 tasks total**: DBA 35, Happy Numbers [Support] 2, Internal 2, Private (no project) 1. DBA tasks carry customer-prefixed titles like `[Sweatcoin] SWEATCOIN-96`, `[Tabby] TABBY-119` etc. All DBA tasks are assigned to Ilya Kosmodemiansky. To see tasks grouped by project add Group By → Project from the search panel; the four groups then show with their counts and aggregate Time Spent. The "Tasks" top-nav button reveals a dropdown with "My Tasks" and "All Tasks" — My Tasks applies an additional assignee=current-user filter.

### Odoo OWL app introspection — action domain/context (Jun 2026)

To read the current action's domain and context from the Playwright browser context: `window.owl.App.apps` is a Set (size 1 in saas-19.3); iterate it and access `app.env.services.action.currentController.action.{id,name,domain,context}`. Returns the live action object including any hardcoded server-side domain. Useful for diagnosing why records are missing from a view without guessing.

### Odoo Helpdesk — SLA deadlines blank on migrated tickets (Jun 2026)

Tickets migrated from JSM via the `odoo_load_*_helpdesk.py` scripts have an empty `SLA Deadline` column in the list view and no SLA widget on the ticket form. The SLA policy exists (visible as "SLAs" in Group By options and the `sla_deadline` field is in the list schema) but the clock never starts because Odoo stamps the SLA deadline at ticket-creation time based on the configured policy — migrated tickets bypassed that trigger. This is expected for historical data; SLA deadlines will populate normally on new tickets opened through the Helpdesk portal. The "SLA Dead…" column header IS present in the list view (confirming the policy feature is active on the team), but all values are null.

### Odoo Helpdesk tickets — tag structure after JSM migration (Jun 2026)

After the Happy Numbers + Sweatcoin PoC imports, the DBA Support team (id 17) at `/odoo/helpdesk/17/tickets` shows two categories of tags on every kanban card: (1) a **request-type tag** (Incident, Issue, Maintenance Task, Create a support ticket, Investigate a problem) and (2) a **customer tag** (Tabby, Sweatcoin, FinteqHub, Sanek, Happy, BridgeIT, IntegraDev, Lime, Sweat Foundation). Zero tags contain "JSM:" text — the prefix was intentionally omitted from the tag names. Kanban cards render the customer tag in a distinct color (each customer tag gets its own color index). The list view Group By Tags shows 14 tag groups: 5 request-type + 9 customer, all plain names. Ticket titles all carry a `[Customer]` prefix (e.g. `[Tabby] …`, `[Sweatcoin] …`).

### Odoo 19 Project kanban — Done/Canceled columns fold by default; Unfold button uses "Unfold Unfold" aria-name

In `project.task` kanban view, stages marked as "folded" (Done, Canceled) render as collapsed columns showing only the count. The Unfold button has `name="Unfold Unfold"` in the accessibility tree — use `page.getByRole('button', { name: 'Unfold Unfold' })` or its snapshot ref. After unfolding, each card is a `<link>` element whose accessible name contains the full task title including the `[Customer]` prefix, the partner name, and the tag name all concatenated. Navigate directly to `/odoo/project/<id>/tasks` to land on the kanban view (not the project form).

### Odoo Online — database backup download via My Subscription page (Jun 2026)

The "Download backup" button is NOT on `https://www.odoo.com/my/databases`. The flow is: gear icon next to the database name → "Manage" → navigates to `https://dataegret.odoo.com/odoo/my-subscription` → the management UI is in a cross-origin iframe from `https://www.odoo.com/my/database?token=...`. The "Download Backup" element inside the iframe is an `<a role="button" class="btn btn-light w-20">` (not a real `<button>`), so `frame.locator('button:has-text(...)')` does NOT find it — use `frame.evaluate(() => Array.from(document.querySelectorAll('a')).find(a => a.textContent.trim() === 'Download Backup'))` to get the href. The token in the URL is time-limited (expires in under ~2 min) — extract and use it immediately. Reliable download pattern: get fresh href from the frame, then inject a synthetic `<a download>` click into the **main page** context (not the iframe), and intercept via `page.waitForEvent('download', {timeout: 300000})`. File is named `dataegret.dump.zip` and contains `dump.sql` (~46 MB uncompressed) + `filestore/` tree.

### Atlassian / Jira — dataegret.atlassian.net profile login confirmed (Jun 2026)

The persistent profile is authenticated to `dataegret.atlassian.net` as `ik@dataegret.com`. On first navigate the browser briefly redirects through `id.atlassian.com/login` but then completes automatically (session cookie is live) — the screenshot call forces the redirect to finish and the page lands on `/jira/for-you`. Do NOT report LOGIN REQUIRED on the redirect; snapshot after the screenshot to confirm. The site name shown in the top bar is "Data Egret customers portal". The full projects list is at `/jira/projects?page=N&sortKey=name&sortOrder=ASC` (3 pages, 52 spaces total). The Jira instance uses the "Spaces" label for projects.

### Odoo 19 contacts import — Tag filter via search autocomplete (Jun 2026)

To filter Contacts by tag in Odoo 19 list view: click the search input, type the tag name character-by-character using `browser_press_key` (NOT `browser_type`/`fill` — those don't trigger autocomplete), wait 1s after each few chars, then use `browser_evaluate` to find the `[role="menuitem"]` item containing "Tag" in `.o_searchview_autocomplete` and click it. The facet will appear as "Tag: <value>" and the pager count updates immediately. Domain-URL filtering (`?domain=[...]`) does NOT work in Odoo 19 — it silently ignores the param. The Notes field for a contact is on the "Notes" notebook tab (not visible in the main form), accessible via `.o_notebook_tab` click then `[name="comment"] .odoo-editor-editable`.

### Odoo 19 import wizard — contacts file confirmation (Jun 2026)

For the easybill migration: `odoo_import_1_companies.csv` (40 companies, 13 columns) and `odoo_import_2_contacts.csv` (29 contact persons, 6 columns) both pass Test with "Everything seems valid" and import cleanly. The `parent_id/id` column auto-maps to "Related Company / External ID" — no manual remapping needed. After importing both files, total tagged contacts = 69 (40 + 29); the 2 pre-existing records (Data Egret GmbH, Ilya Kosmodemiansky) have no easybill tag so overall list = 71.

### Odoo 19 import wizard — `is_company` boolean not importable via wizard UI (Jun 2026, updated)

In Odoo 19 (saas-19.3), the `res.partner` import wizard does NOT expose the boolean `is_company` field (company vs individual flag) under any label in its field picker — not "Is a Company", "Company Type", "Individual", or "is_company". Exhaustively confirmed via searches for "company", "is_company", "Is a Company", "individual", and "type". The "Company" field in the wizard is a many2one to `res.company` (the owning tenant company), NOT the boolean. The "Address Type" field (from the "type" search) maps to `company_type` selection (contact/delivery/invoice/etc.), also not the boolean. **The boolean `is_company` field is simply absent from the import wizard field list.** Workaround: import without the flag (records land as Individuals), then batch-update via script/API, OR use the Odoo RPC `load()` method directly which respects `is_company`. A CSV column named `is_company` with `True` auto-maps to the wrong "Company" many2one and fails Test with "No matching record found for name 'True' in field 'Company'". Additionally, `base_vat` enforces GB VAT format as `GB123456782` (9 digits); 8-digit values cause a hard blocking Test error.

### Odoo 19 import wizard — ref-based Playwright selectors fail intermittently

The `mcp__playwright-persistent` tool's `ref=eNNN` selectors throw "Unknown engine" errors after page navigation in the Odoo import wizard context. Fall back to `browser_evaluate` with DOM queries (`document.querySelector`, `Array.from(...).find(b => b.textContent.includes(...))`) for all interactions in the wizard. The file-chooser flow works normally: evaluate to click the `input[type="file"]`, then `browser_file_upload` catches the chooser.

### Odoo migration program — sites and UI export paths (Jun 2026)

The `odoo-migration-manager` agent (consolidating Jira Service Management, Pipedrive, and easybill into Odoo Online) dispatches browser work here only when no API path exists. Sites involved — none confirmed in the profile yet, so expect first-run LOGIN REQUIRED → `browser-profile-setup.sh`: the Odoo Online instance (`<company>.odoo.com`; data import lives on any model's list view under the ⚙/Action menu → "Import records"), Pipedrive (`app.pipedrive.com`; bulk export at account menu → Tools and apps → Export data, XLSX/CSV, generated exports downloadable 28 days; API token page at Settings → Personal preferences → API), Atlassian admin (`admin.atlassian.com`; JSM portal-only customers CSV under User management → Jira Service Management → Export customers; issue-navigator CSV export caps at 10,000), and easybill (`www.easybill.de` login; customer/document CSV exports and bulk "ZIP with all documents" PDF download under document evaluations; API key under Profile and Settings → API Key). Hard rule for this program: **source systems (Pipedrive, Jira/Atlassian, easybill) are read-only** — export clicks only, never edit/delete/close anything there; writes happen only in Odoo, and only on its test-duplicate databases unless the prompt explicitly says production.

### Google Calendar — week view DOM structure and measurements (Jun 2026, dark theme)

Captured at https://calendar.google.com/calendar/u/0/r/week (account ik@dataegret.com). The page renders at 1200px viewport width but the internal grid is ~2930px wide (7 × 313px day columns + 369px left offset). Key selectors: `.BiKU4b` = day column (7 of them, 81px visible but 313px logical); `.aLC8Le` = time-gutter placeholder (24 sJ9Raf children, each 40px tall = 40px per hour); `.RuAPDb.tkd8cb` = scrollable container holding hour labels (24-hour format, "23:00"…"22:00"); `.rGFpCd` = current-time line (2px solid rgb(245,94,87) border-top); `.LvQ60d` = current-time red dot (12×12px circle, rgb(245,94,87)); `.BiKU4b.F262Ye` = today column; event blocks use `[role="button"]` with borderRadius 6px. The `/u/1/` path redirects to the marketing page in this profile — use `/u/0/` for ik@dataegret.com.

### GSC dataegret.com — staging URLs (dev2) appear in production domain property

Because the domain property `sc-domain:dataegret.com` covers all subdomains, `dev2.dataegret.com` URLs surface in the production Page indexing report under "Blocked by robots.txt" (first detected 3/7/26). This is expected behaviour for a domain property — it is NOT a misconfiguration of GSC itself. The staging server's `robots.txt` disallows Googlebot, so these URLs land in the "Blocked" bucket rather than being indexed. The fix, if desired, is to add a separate URL-prefix property for `https://dev2.dataegret.com/` so staging data can be tracked and filtered independently.

### GSC dataegret.com — /popup/ slug URLs return 404 in production

As of Jun 2026, the "Not found (404)" bucket (50 pages) contains multiple `/popup/<russian-slug>/` URLs that return 404 on production — e.g. `/popup/консультирование-postgresql/`, `/popup/политика-конфиденциальности/`, `/popup/запросы-планируются-медленно/`, `/popup/воркеры-автовакуума-работают-не-пере-2/`, `/popup/marketing-assistant/`, `/popup/менеджер-по-продажам/`. These were formerly live popup/modal pages (likely CPT or page builder popups) that have since been deleted or their slugs changed. Also present: `/ultimate-plan/`, `/ru/`, `/en/`, `/news-blog/postgresql-resourses/` (typo slug).

### GSC — Page indexing report snapshot for dataegret.com (Jun 2026 baseline)

Indexed: 287 | Not indexed: 507 (10 reasons). Top reasons: Crawled-not-indexed 305 (Google systems, first detected 5/13/23, long-standing); noindex tag 85 (feeds + date archives, intentional); Not found 404 50 (popup slugs + dead pages); Blocked robots.txt 27 (mostly dev2 staging, first detected 3/7/26); Page with redirect 15; Alternate page with proper canonical 6; Blocked 4xx 2; Duplicate without user canonical 1; Discovered-not-indexed 11; Duplicate Google chose different canonical 5. Enhancements all-valid: Breadcrumbs 58, FAQ 4, Profile page 1.

### Google Cloud Console — OAuth client JSON download requires adding a new secret (2026-06)

The "Download JSON" button on the credentials list page (`/apis/credentials`) is hidden via `cfc-visibility-hidden` but still in the DOM. To surface it: remove that class via `browser_evaluate` then click. However, the downloaded JSON will be missing `client_secret` because Google no longer exposes existing secrets (they show only a masked tail like `****0Shh`). To get a JSON with a real secret: open the client detail page (`/auth/clients/<id>`), click "Add secret", and use the "Download JSON" button that appears inline next to the newly created secret (tagged "NEW"). That download includes the full `client_secret`. The old secret remains active; disable/delete it after confirming the new one works.

### Google Cloud Console — cookie banner blocks Save button on `/auth/scopes`

After closing the "Update selected scopes" dialog, the cookie consent banner (`glue-cookie-notification-bar`) can intercept pointer events and prevent clicking the "Save" button. Click the "Hide" button on the banner first, then click Save.

### Google Cloud Console — persistent profile login behaviour

The profile's Google session may not be active when the browser first opens (the navigate call lands on the accounts.google.com sign-in page), but the session cookie is present and the redirect completes automatically before the next snapshot. Do not report LOGIN REQUIRED on the first redirect; instead take a screenshot (which forces the redirect to finish) and then snapshot again to confirm the actual target page loaded. Verified with account ik@dataegret.com, project tcal-369515.

### Google Cloud Console — OAuth consent screen new layout (Google Auth Platform)

As of mid-2024 the old `/apis/credentials/consent` consent-screen page was replaced by the "Google Auth Platform" section at `/auth/*`. The relevant sub-pages are: `/auth/overview` (metrics + checkup), `/auth/branding` (app name, support email, logo), `/auth/audience` (Internal vs External user type; publishing status), `/auth/clients` (OAuth clients list), `/auth/scopes` (Data Access / configured scopes). The pagination buttons on the scopes table have no aria-label — find them as empty-innerText non-disabled buttons and click the last one for "next page".

### Google Cloud Console — scopes table pagination selector

The "Next page" button in `/auth/scopes` has no aria-label and no visible text (icon only). Use: `buttons.filter(b => !b.getAttribute('aria-label') && b.innerText.trim() === '' && !b.disabled)` then click the last element to advance the page.
