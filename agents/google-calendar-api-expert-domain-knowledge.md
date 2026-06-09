# Google Calendar API Expert — Domain knowledge

Persistent notes accumulated by the `google-calendar-api-expert` agent across invocations. The agent reads this file at the start of every run and appends durable findings — verified API quirks, version-sensitive behavior, doc anchors worth re-finding, and user preferences specific to this domain.

This is distinct from any project `CLAUDE.md`: project specifics live there; what's here is durable cross-project knowledge of the Calendar/Tasks/OAuth domain.

Keep entries terse — a personal cheat sheet, not a textbook. H3 heading + one tight paragraph each. Date version-sensitive facts.

<!-- entries below; newest on top -->

### Console UI rename + consent-screen facts (verified 2026-06-08)

The old "OAuth consent screen" is now **APIs & Services > Google Auth Platform**, split into tabs **Branding / Audience / Clients / Data Access** (renamed ~2024; first visit shows **Get Started**). Scopes are added under **Data Access > Add or remove scopes**; test users under **Audience > Test users > Add users**. Both `calendar.readonly` and `tasks.readonly` are **sensitive** scopes (sensitive-scope verification ~3-5 business days; needed only when published to Production for non-test users). External + Testing publishing status: refresh tokens expire **7 days** after consent (exception: only name/email/profile/openid scopes); test-user cap is **100**. Brand verification (logo/name on consent screen, 2-3 business days) is separate from scope verification. Desktop-app client secret is downloadable only at creation time; redirect URIs are not user-editable for Desktop type (loopback handled automatically). Docs: developers.google.com/workspace/guides/configure-oauth-consent, developers.google.com/identity/protocols/oauth2#expiration, support.google.com/cloud/answer/15549257.

### Seed: installed-app loopback flow, read-only scopes, multi-account free/busy (seeded 2026-06-08)

Desktop apps use the **loopback redirect** (`http://127.0.0.1:<port>`), not the deprecated OOB flow; pair with PKCE + a `state` nonce. Get a refresh token only with `access_type=offline` + `prompt=consent` on first authorization — persist it per account as a secret at rest. Read-only viewing = `calendar.readonly` + `tasks.readonly`. For "when am I free" across accounts: union each account's busy intervals; `freebusy.query` is cleaner than `events.list`+merge when you don't need event detail, but it returns no detail and caps calendars per call. `events.list` with `singleEvents=true&orderBy=startTime` expands recurrences in order; all-day uses `date`, timed uses `dateTime`+`timeZone`. Incremental sync via `nextSyncToken`; a `410 Gone` means discard the token and full-resync. (Verify all against live `developers.google.com` docs each run — Google deprecates and renames.)
