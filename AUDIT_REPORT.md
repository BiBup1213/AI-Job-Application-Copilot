# AI Job Application Copilot Audit Report

Date: 2026-06-01

Scope: repository audit only. No feature implementation was performed.

## 1. Mock/demo data

### Frontend

| File path | What is mocked / hardcoded | Keep as fallback or replace with API data |
|---|---|---|
| `frontend/src/mockDashboardData.ts` | Sidebar navigation labels and icons only. No job/campaign/mail/KPI mock records remain in this file. | Keep. This is UI configuration, not business data. |
| `frontend/src/App.tsx` | `defaultCampaignForm` pre-fills the new campaign modal with `"Python Entwickler (Junior)"`, `"Python, Django, REST, Junior"`, `"LinkedIn, StepStone"`, etc. | Replace defaults with empty values or user/profile-derived defaults. Could keep only as development placeholder. |
| `frontend/src/App.tsx` | Header badge always says `Gmail verbunden`. | Replace with backend/account integration state later. For MVP it is misleading unless Gmail is actually connected; backend is simulated only. |
| `frontend/src/App.tsx` | Sidebar user block is hardcoded: initials `MB`, `Max Beispiel`, `max.beispiel@gmail.com`. | Replace with profile/user API later. Acceptable visual placeholder for MVP if documented. |
| `frontend/src/App.tsx` | Empty-state text: “Noch keine Jobs...”, “Noch keine Suchkampagnen...”, “Noch keine E-Mails...” | Keep. These are UI fallback states, not mock data. |
| `frontend/src/App.tsx` | Job detail fallback strengths/risks/application angle when `job.match` is missing. | Should remain as a defensive fallback, but the preferred fix is to ensure jobs get evaluated so `match` exists. |
| `frontend/src/App.tsx` | KPI subtitles are static labels like `Aus dem Backend`, `Bewerbungen`, `Gesamt`, `Mail-Zentrale`, `Nächste 7 Tage`. | Keep as UI labels, but review wording once metrics are finalized. |
| `frontend/src/App.tsx` | Pipeline columns are hardcoded status groups: `Neu`, `Entwurf`, `Beworben`, `Antwort`. Cards are backend-derived from applications. | Keep grouping config. Cards should stay API-derived. |
| `frontend/src/App.tsx` | “Heute wichtig” task titles are generated from frontend-derived counts, not backend `next_actions`. | Replace or reconcile with `GET /api/dashboard/summary/` `next_actions` once task logic is centralized. |
| `frontend/src/App.tsx` | `Alle anzeigen` links/buttons are visual only. | Replace with real navigation when routing exists. |

### Backend

| File path | What is mocked / demo | Keep as fallback or replace with API data |
|---|---|---|
| `backend/ai_services/services.py` | `evaluate_job_match()` is deterministic mock scoring. It includes fixed scores for TRIOLOGY, KOSATEC, Beispiel Commerce, Stadt Wolfenbüttel. | Keep for MVP. Replace service internals later with LLM/scoring integration behind same interface. |
| `backend/ai_services/services.py` | `generate_application_documents()` creates deterministic German cover letter/email text. | Keep for MVP. Replace service internals later; preserve human approval flow. |
| `backend/ai_services/services.py` | `classify_email_message()` keyword-based mock classification. | Keep for MVP. Replace later with real classifier/LLM. |
| `backend/ai_services/services.py` | `create_mock_jobs_for_campaign()` creates fixed mock jobs and does not scrape job boards. | Keep only for MVP. Replace with real job-source adapters later. |
| `backend/ai_services/services.py` | `sync_mock_email_messages()` creates fixed mock emails and does not call Gmail. | Keep only for MVP. Replace with Gmail API later. |
| `backend/ai_services/management/commands/seed_demo_data.py` | Seeds demo campaigns, jobs, applications, documents, emails, status events. | Keep as demo/development command. Do not use as production data source. |

## 2. API integration

### Backend endpoints that exist

Router/API paths from `backend/config/urls.py`, viewsets, and URL modules:

- `GET /api/dashboard/summary/`
- `GET /api/campaigns/`
- `POST /api/campaigns/`
- `GET /api/campaigns/{id}/`
- `PATCH /api/campaigns/{id}/`
- `POST /api/campaigns/{id}/run/`
- `GET /api/jobs/`
- `GET /api/jobs/{id}/`
- `POST /api/jobs/{id}/evaluate/`
- `POST /api/jobs/{id}/create-application/`
- `GET /api/applications/`
- `POST /api/applications/`
- `GET /api/applications/{id}/`
- `PATCH /api/applications/{id}/`
- `POST /api/applications/{id}/generate-documents/`
- `POST /api/applications/{id}/approve-document/`
- `POST /api/applications/{id}/create-gmail-draft/`
- `POST /api/applications/{id}/mark-applied/`
- `GET /api/mail/messages/`
- `GET /api/mail/messages/{id}/`
- `POST /api/mail/messages/{id}/classify/`
- `POST /api/mail/sync/`
- `GET /admin/`

### Endpoints used by the frontend

Used from `frontend/src/api/*` and `frontend/src/App.tsx`:

- `GET /api/dashboard/summary/`
- `GET /api/jobs/`
- `GET /api/campaigns/`
- `POST /api/campaigns/`
- `POST /api/campaigns/{id}/run/`
- `GET /api/applications/`
- `POST /api/applications/{id}/generate-documents/`
- `POST /api/applications/{id}/approve-document/`
- `POST /api/applications/{id}/create-gmail-draft/`
- `GET /api/mail/messages/`
- `POST /api/mail/sync/`
- `POST /api/jobs/{id}/create-application/`

### Endpoints defined in frontend API modules but unused by UI

- `POST /api/jobs/{id}/evaluate/` via `evaluateJob()` in `frontend/src/api/jobs.ts`
- `POST /api/mail/messages/{id}/classify/` via `classifyMailMessage()` in `frontend/src/api/mail.ts`

### Backend endpoints currently unused by frontend

- `GET /api/campaigns/{id}/`
- `PATCH /api/campaigns/{id}/`
- `GET /api/jobs/{id}/`
- `POST /api/jobs/{id}/evaluate/`
- `POST /api/applications/`
- `GET /api/applications/{id}/`
- `PATCH /api/applications/{id}/`
- `POST /api/applications/{id}/mark-applied/`
- `GET /api/mail/messages/{id}/`
- `POST /api/mail/messages/{id}/classify/`

### Frontend actions that call the backend

- Initial dashboard load calls summary, jobs, campaigns, mail messages, applications.
- `Bewerbung erstellen` calls `POST /api/jobs/{id}/create-application/`, then `POST /api/applications/{id}/generate-documents/`.
- `Gmail-Entwurf erstellen` may call `POST /api/jobs/{id}/create-application/`, `POST /api/applications/{id}/generate-documents/`, `POST /api/applications/{id}/approve-document/`, then `POST /api/applications/{id}/create-gmail-draft/`.
- `Neue Suchkampagne` opens local modal state.
- Campaign submit calls `POST /api/campaigns/`, then `POST /api/campaigns/{id}/run/`.
- `Synchronisieren` calls `POST /api/mail/sync/`.
- Error retry calls the initial dashboard load again.

### Actions that only change local state or are visual only

- Selecting a job card changes local selected ID.
- Opening/closing campaign modal is local state.
- Notice banner dismiss is local state.
- `Alle anzeigen` buttons do not navigate.
- Sidebar navigation buttons do not navigate.
- Pipeline cards are not clickable.
- Heute-wichtig rows are not wired to actions.
- Bookmark/more icons in detail panel are visual only.
- “Nach Match-Score” dropdown is visual only.

### TypeScript/API response mismatches and risks

- `JobPostingDto.requirements`, `nice_to_have`, and `tags` are typed as `string[]`, but backend `JSONField` does not enforce array shape. Safe for seeded data, risky for arbitrary data.
- `SearchCampaignDto.keywords`, `industries`, `sources`, `exclude_keywords` are typed as `string[]`, but backend `JSONField` does not enforce array shape. Frontend submit sends arrays, but API could return malformed JSON from admin/manual writes.
- `DashboardSummary.top_matches`, `applications_total`, `emails_requiring_attention`, and `next_actions` are typed and fetched but largely unused by the dashboard.
- KPI “Beworben” uses `summary.applications_by_status.applied` when summary exists, so it excludes `gmail_draft_created` and `follow_up_due` even though the fallback includes them. This makes the metric inconsistent.
- Campaign run creates jobs without `JobMatch`; frontend maps missing scores to `0%`. Because the UI never calls `evaluateJob()`, newly created mock campaign jobs can appear with `0%` until manually evaluated elsewhere.
- `Gmail-Entwurf erstellen` auto-approves an email document before creating the draft. This conflicts with the stated human-in-the-loop principle, even though it satisfies backend requirements.

## 3. UI interactions

| Interaction | Status | Notes |
|---|---|---|
| Selecting a job card | Working | Updates local selected job and detail panel. |
| Bewerbung erstellen | Partial | Calls backend and generates documents. It does not open an application/document review screen afterward. |
| Gmail-Entwurf erstellen | Partial | Calls backend flow, but auto-approves the email document to satisfy the API. Human approval is effectively bypassed. |
| Neue Suchkampagne | Working | Opens modal. |
| Submitting a campaign | Working/partial | Creates campaign and runs mock search. Sources are free-text, and created jobs may lack match scores. |
| Mail sync / Synchronisieren | Working | Calls mock backend sync and reloads dashboard data. |
| Alle anzeigen links | Visual only | Buttons have no routing/action. |
| Sidebar navigation | Visual only | No routing and no active state changes beyond hardcoded `Übersicht`. |
| Pipeline cards | Visual only | Backend-derived display, but no click/detail behavior. |
| Heute wichtig items | Visual only | Frontend-derived display, no click/action behavior. |
| Stelle öffnen | Partial | Opens `source_url`; seeded/mock URLs are `example.test`, so this is not useful for real applications yet. |
| Nach Match-Score dropdown | Visual only | No sorting menu or alternate sort. |
| Detail bookmark/more icons | Visual only | No action. |

## 4. Navigation

No real routing exists. `frontend/package.json` does not include `react-router-dom`, and there are no `BrowserRouter`, `Routes`, or `Route` components. The app is a single dashboard view.

Recommended minimal React Router pages later:

- `/` or `/uebersicht` -> `Übersicht`
- `/suchkampagnen` -> `Suchkampagnen`
- `/jobs` -> `Gefundene Jobs`
- `/bewerbungen` -> `Bewerbungen`
- `/mail` -> `Mail-Zentrale`
- `/follow-ups` -> `Follow-ups`
- `/profil` -> `Profil`
- `/einstellungen` -> `Einstellungen`

Minimum implementation recommendation:

- Add `react-router-dom`.
- Convert sidebar items to `NavLink`.
- Keep the current dashboard as `OverviewPage`.
- Start with placeholder pages that reuse existing panels/data rather than building new features immediately.

## 5. Search campaign form

Current modal fields in `frontend/src/App.tsx`:

- `name`
- `location`
- `keywords`
- `industries`
- `sources`
- `exclude_keywords`
- `radius_km`
- `remote_allowed`
- `hybrid_allowed`

Backend mapping:

- `name` maps correctly to `SearchCampaign.name`.
- `location` maps correctly to `SearchCampaign.location`.
- `radius_km` maps correctly to `SearchCampaign.radius_km`.
- `remote_allowed` maps correctly to `SearchCampaign.remote_allowed`.
- `hybrid_allowed` maps correctly to `SearchCampaign.hybrid_allowed`.
- `keywords` maps to `SearchCampaign.keywords`, but UI stores comma-separated text and converts with `splitCsv()`.
- `industries` maps to `SearchCampaign.industries`, but UI stores comma-separated text and converts with `splitCsv()`.
- `sources` maps to `SearchCampaign.sources`, but UI stores comma-separated text and converts with `splitCsv()`.
- `exclude_keywords` maps to `SearchCampaign.exclude_keywords`, but UI stores comma-separated text and converts with `splitCsv()`.

Sources are currently text input only, not selectable.

Recommended improved fields:

- Campaign name text input.
- Keywords token input/chip editor.
- Industries token input/chip editor.
- Sources as checkboxes:
  - Arbeitsagentur
  - StepStone
  - Indeed
  - LinkedIn
  - XING
  - Unternehmensseiten
  - Manuelle Eingabe
- Location text input.
- Radius numeric input/slider.
- Remote allowed checkbox/toggle.
- Hybrid allowed checkbox/toggle.
- Exclude keywords token input/chip editor.
- Optional status hidden/default `draft`.

## 6. Backend

### Models

- `SearchCampaign`: matches requested MVP fields and uses JSON fields for keyword/source arrays.
- `JobPosting`: matches requested MVP fields.
- `JobMatch`: one-to-one with job, score validators 0-100, category choices A/B/C/X.
- `Application`: status choices implemented, FK to job, timestamps.
- `ApplicationDocument`: document type choices, versioning, approval flag.
- `EmailMessage`: optional FK to application, classification choices.
- `StatusEvent`: FK to application and old/new status fields.

### Serializers

- Basic DRF `ModelSerializer` coverage exists for all major resources.
- Nested read-only documents/status events are included on applications.
- Nested match is included on jobs.
- JSON fields are not shape-validated beyond default DRF JSON handling.

### Viewsets/endpoints

- Campaign, job, application, mail, and dashboard endpoints exist.
- `JobPostingViewSet` is read-only plus custom evaluate/create-application actions.
- `ApplicationViewSet` supports get/patch/post and custom workflow actions.
- `EmailMessageViewSet` is read-only plus classify action.
- Dashboard summary is an API view.

### Migrations

- Initial migrations exist for campaigns, jobs, applications, and mailcenter.
- `ai_services` has no models and only an empty migrations package.

### Seed command

- `python manage.py seed_demo_data` exists.
- Seeds the requested jobs, campaigns, applications, emails, documents, and status events.
- It is demo-oriented and deterministic.

### Admin registration

- Admin registration exists for SearchCampaign, JobPosting, JobMatch, Application, ApplicationDocument, StatusEvent, and EmailMessage.

### Campaign run

- `POST /api/campaigns/{id}/run/` calls `create_mock_jobs_for_campaign()`.
- It creates fixed mock jobs and marks the campaign active.
- It does not scrape real job boards.
- It does not create/evaluate `JobMatch` entries for created jobs.

### Application creation

- `POST /api/jobs/{id}/create-application/` uses `get_or_create()` and creates a `StatusEvent` only when new.
- It returns existing application if one already exists.

### Document generation

- `POST /api/applications/{id}/generate-documents/` creates cover letter and email documents.
- It increments versions per document type.
- It moves status from `new`/`interesting` to `draft_open` and creates a status event.

### Simulated Gmail draft

- `POST /api/applications/{id}/create-gmail-draft/` requires an approved email document.
- It sets status to `gmail_draft_created` and records a status event.
- It does not send email or call Gmail API.

### Mail sync

- `POST /api/mail/sync/` creates fixed mock emails and classifies newly created ones.
- It does not call Gmail API.
- Existing mock emails are returned but not reclassified.

### Status events

- Created for application creation, status patch changes, document generation, document approval, Gmail draft creation, and mark-applied.
- There is no status event for returning an existing application from `create-application`.

## 7. Data consistency

| Dashboard area | Source | Consistency notes |
|---|---|---|
| KPI cards | Mixed backend-derived and frontend-derived | `Neue passende Jobs` uses total jobs, not necessarily new/matching. `Beworben` is inconsistent because summary path counts only `applied`; fallback counts more statuses. `Antworten` uses mail count, not `emails_requiring_attention`. |
| Job ranking | Backend-derived | Jobs come from `/api/jobs/`; score/detail from nested `match`. Missing matches become `0%` with fallback text. |
| Detail panel | Backend-derived with frontend fallback | Uses selected API job and nested match. Strengths/risks/angle fallback is hardcoded if no match exists. |
| Campaigns | Backend-derived | Display count is campaign status (`aktiv`, `Entwurf`), not “23 neu” style new job counts. |
| Mails | Backend-derived | Sender display is derived from email address and may look less realistic than seeded names. |
| Pipeline | Frontend-derived from backend applications | Columns and status grouping are hardcoded; cards are application-derived. |
| Heute wichtig | Frontend-derived from backend applications/mail | Does not use backend `dashboard_summary.next_actions`; counts are recomputed in frontend. |
| Sidebar/profile/Gmail badge | Hardcoded | Not connected to backend or auth. |

## 8. Prioritized fixes

### P0: must fix for MVP

- Ensure jobs created by campaign runs get evaluated automatically, or call `POST /api/jobs/{id}/evaluate/` after campaign run. Otherwise new jobs can show `0%`.
- Stop auto-approving email documents in the `Gmail-Entwurf erstellen` frontend flow. Require explicit human approval or provide a clear approval step.
- Make KPI definitions consistent and backend-owned. At minimum fix `Beworben`, `Antworten`, and `Neue passende Jobs` semantics.
- Add source selection checkboxes to the campaign form to prevent invalid/free-form source values.
- Add basic navigation/routing or remove visual-only navigation affordances until routing exists.

### P1: important usability fixes

- Wire `Alle anzeigen` links to real pages once routing exists.
- Add detail pages or side panels for applications, campaigns, mail messages, pipeline cards, and today-important tasks.
- Use `dashboard_summary.next_actions` or move task calculation fully backend-side.
- Add JSON shape validation in serializers for array fields.
- Add frontend handling for `GET /api/jobs/{id}/`, `GET /api/applications/{id}/`, and `PATCH /api/applications/{id}/` when detail/edit pages exist.
- Add explicit “mark applied” UI for `POST /api/applications/{id}/mark-applied/`.

### P2: polish/later

- Replace hardcoded user block and Gmail badge with account/profile state.
- Add real sort/filter controls for job ranking.
- Replace mock logo generation with company avatars or initials consistently.
- Improve campaign status display with counts of newly created jobs.
- Add pagination or search as data grows.
- Add tests for frontend API mapping and backend workflow endpoints.

## Verification run

The requested checks were run after creating this audit report:

- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- `python3 -m compileall -q backend`

Results are summarized in the final assistant response for this task.
