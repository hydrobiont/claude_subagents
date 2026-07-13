# Pipedrive API Expert — Domain knowledge

Persistent notes accumulated by the `pipedrive-api-expert` agent across invocations. The agent reads this file at the start of every run and appends durable findings — verified Pipedrive API behavior and quirks, Data Egret's own account structure (pipelines, stages, custom-field hashes, users, counts, sources), and doc anchors worth re-finding.

**Never stored here:** the API token or any secret value (keychain only), ephemeral task state (that lives in `~/work/de/odoo/migration/CLAUDE.md` + `PLAN-pipedrive-crm.md`), or generic best practices. See the agent definition (`pipedrive-api-expert.md`) and `PLAN-pipedrive-crm.md`.

**HARD RAIL: Pipedrive is READ-ONLY — GET calls only, never write.**

<!-- entries below; newest on top -->

### 2026-07-02 — Verified account structure + API access (via scripts/pipedrive_probe.py)

**Access.** Account **Data Egret GmbH**, company slug `dataegret`, host `dataegret.pipedrive.com`. User Ilya Kosmodemiansky is **admin** (sees all data). Token in keychain `pipedrive-dataegret-api` / `ik@dataegret.com` (40-char personal API token); domain in `pipedrive-dataegret-domain`. **Auth: `x-api-token` header works** (preferred); `?api_token=` query param is the fallback. Base URLs `https://dataegret.pipedrive.com/api/v1/…` and `/api/v2/…`.

**Rate budget (observed headers).** `x-ratelimit-limit: 100`, `x-ratelimit-remaining: 99` → ~100-request burst window. No `x-daily-requests-left` surfaced on the probe — daily token budget ≈ plan × seats; **confirm exact plan tier & seat count with the user** (still outstanding).

**The 10 pipelines (verified ids).**

| id | name | CRM scope |
|----|------|-----------|
| 10 | Sales Qualified | IN — primary funnel → Odoo **Sales** team |
| 14 | Courses | IN — this IS the user's "Trainings"; web-form fed → Odoo **Trainings** team |
| 9  | Long shots | IN — the user's "long shorts" → Sales or Unsorted |
| 4  | Current customers | IN → Unsorted/Legacy |
| 5  | Black List | IN → Unsorted/Legacy |
| 6  | Recomendations *(sic)* | IN → Unsorted/Legacy |
| 7  | Cold (Interesting but w/o contacts) | IN → Unsorted/Legacy |
| 8  | Whitepapers | IN → Unsorted/Legacy |
| 12 | Subscriptions | OUT of CRM per PLAN (billing in easybill→Invoicing) — confirm whether deal records should still be archived |
| 13 | Subscriptions renew | OUT of CRM per PLAN — same |

**Colloquial → real names** (user dictates by voice): "Trainings" = **Courses** (14); "long shorts" = **Long shots** (9); "Sales Qualified" = its own name (10).

**Counts (verified).** **410 deals** (`deals/summary.total_count`); **54 stages** across the 10 pipelines. persons, organizations, deals, leads, notes, files, activities, and mailbox mail threads all returned data (≥1 each, with more available).

**Entity reachability (200 OK, read-only, token has access).** `users/me`, `pipelines`, `stages`, `deals` (v1 + v2), `persons`, `organizations`, `leads`, `notes`, `files`, `activities`, `mailbox/mailThreads`.

**API mechanics.** v1 mid-sunset; **v1-only (extract FIRST):** notes, files, users, leads, mailbox(mail). v2 for deals/persons/orgs/pipelines/stages/activities. Pagination: v1 `start`/`limit` + `more_items_in_collection`/`next_start`; v2 cursor (`next_cursor`). Custom fields = 40-char hex hash keys → resolve via `dealFields`/`personFields`/`organizationFields`. Files + mail attachments = separate binary downloads (manifest per parent).

**Odoo target mapping (per PLAN-pipedrive-crm.md).** pipeline→`crm.team`; stage→`crm.stage` (team-pinned); deal→`crm.lead` type=opportunity; lead→`crm.lead` type=lead; won→`is_won` stage; lost→`active=False`+`lost_reason`; org→`res.partner` company; person→`res.partner` individual (`parent_id`=org); source incl. web forms→`utm.source`/`source_id`; owner→`user_id` via `pd_user_crosswalk`; email→chatter `mail.message` (no-send); note→chatter; activity done→chatter log, open→`mail.activity`; file→`ir.attachment`. **External IDs** (module `migration`): `pd_org_<id>`, `pd_person_<id>`, `pd_deal_<id>`, `pd_lead_<id>`, `pd_activity_<id>`, `pd_note_<id>`, `pd_mail_<id>`, `pd_file_<id>`, `pd_user_<san>`, `pd_team_<pipelineId>`, `pd_stage_<id>`, `pd_source_<san>`.

**Confirmed migration decisions (2026-07-02).** All contacts imported + tagged `Pipedrive`, dedup deferred to a later research pass. All deals across in-scope pipelines (won/lost/open); Subscriptions (12) + Subscriptions renew (13) OUT of CRM. **Leads layer ON** (Leads Inbox → Odoo Leads; web forms → Leads). Activities full (done→chatter log, open→scheduled `mail.activity`). Emails + files full fidelity via the proven no-send chatter path (`mail.message.create()`, no `partner_ids`, guard aborts on any mail/notification delta). Structure = per-pipeline Sales Teams (Sales ← 10, Trainings ← 14) + Unsorted/Legacy catch-all.

**Still to inventory in Phase 0 (append when known).** Stage names + per-pipeline order (54 stages) + each stage's `is_won` flag; users list → `pd_user_crosswalk`; custom-field hash→label maps (deal/person/org); deal `source`/origin vocabulary (esp. the Courses web-form channel); real per-entity counts (persons, orgs, leads, files, notes, activities, mail).
