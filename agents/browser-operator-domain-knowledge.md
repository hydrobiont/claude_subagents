# Browser Operator — Domain knowledge

Persistent notes accumulated by the `browser-operator` agent across invocations. The agent reads this file at the start of every run and appends entries when it learns something durable about the domain — e.g. quirks of specific admin panels, selectors that change over time, sites that fight Playwright in known ways, authentication patterns that persist via the dedicated profile, etc.

See the agent definition (`browser-operator.md`) for the rules on what belongs here vs not.

<!-- entries below; newest on top -->

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
