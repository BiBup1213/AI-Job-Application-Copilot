# AI Job Application Copilot

Fullstack MVP foundation for a human-in-the-loop job application assistant.

The project includes a Django REST API with deterministic mock AI services, SQLite local development, Django Admin, demo data, and a React/Vite/Tailwind dashboard frontend connected to the API.

## Structure

```text
backend/
frontend/
README.md
```

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

If your system exposes Python as `python3`, use `python3 -m venv .venv`.

The API runs at `http://127.0.0.1:8000/api/`.

Keep this terminal running while using the frontend.

AI services use a provider selector:

```text
AI_PROVIDER=mock
OPENAI_API_KEY=
OPENAI_MODEL=
```

The deterministic mock provider is the default. With `AI_PROVIDER=openai`,
job matching can call OpenAI when `OPENAI_API_KEY` and `OPENAI_MODEL` are set.
Document generation and email classification still delegate to mock behavior.
If OpenAI configuration is missing, parsing/validation fails, or the provider
errors, the backend logs a warning and falls back to mock. API keys are not logged.

## Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The frontend runs at `http://localhost:5173/` and calls the backend from:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

If the backend is unavailable, the dashboard shows a clean error state instead of crashing.

The sidebar uses React Router routes for Übersicht, Suchkampagnen, Gefundene Jobs, Bewerbungen, Mail-Zentrale, Follow-ups, Profil, and Einstellungen. Profil and Einstellungen remain placeholders; the core MVP workflow pages use backend data.

## Current Features

- Manual job import from the dashboard and `Gefundene Jobs` page. Imported jobs are stored through the backend and immediately evaluated with the deterministic mock matching service.
- Campaign mock search with automatic deterministic job matching.
- Human-in-the-loop application document review, editing, and approval.
- Simulated Gmail draft creation after explicit E-Mail document approval.
- `Bewerbungen` page with status filters, quick actions, follow-up dates, notes, and links into the document review/detail view.
- `Mail-Zentrale` page with mock sync, reclassification, application linking, and explicit status-update suggestions.
- `Follow-ups` page with due/planned follow-ups, German follow-up drafts, and explicit review/approval.

## Not Implemented Yet

- No real Gmail API integration.
- No real job board scraping.
- No real AI/LLM document generation, follow-up drafting, or mail classification.
- No real email sending.
- No authentication or multi-user profile management.

See `TESTING.md` for the manual MVP test checklist.

## Run Backend And Frontend Together

Terminal 1:

```bash
cd backend
source .venv/bin/activate
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

Terminal 2:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open:

```text
http://localhost:5173/
```

The frontend uses these API calls:

- `GET /api/dashboard/summary/`
- `GET /api/jobs/`
- `POST /api/jobs/manual-import/`
- `GET /api/campaigns/`
- `GET /api/applications/`
- `GET /api/applications/{id}/`
- `PATCH /api/applications/{id}/`
- `GET /api/mail/messages/`
- `POST /api/jobs/{id}/create-application/`
- `POST /api/applications/{id}/generate-documents/`
- `POST /api/applications/{id}/generate-follow-up/`
- `POST /api/applications/{id}/approve-document/`
- `PATCH /api/applications/{id}/documents/{document_id}/`
- `POST /api/applications/{id}/create-gmail-draft/`
- `POST /api/applications/{id}/mark-applied/`
- `POST /api/campaigns/`
- `POST /api/campaigns/{id}/run/`
- `POST /api/mail/sync/`
- `PATCH /api/mail/messages/{id}/`
- `POST /api/mail/messages/{id}/classify/`

## Main API Endpoints

```text
GET  /api/dashboard/summary/

GET  /api/campaigns/
POST /api/campaigns/
GET  /api/campaigns/{id}/
PATCH /api/campaigns/{id}/
POST /api/campaigns/{id}/run/

GET  /api/jobs/
GET  /api/jobs/{id}/
POST /api/jobs/manual-import/
POST /api/jobs/{id}/evaluate/
POST /api/jobs/{id}/create-application/

GET  /api/applications/
GET  /api/applications/{id}/
PATCH /api/applications/{id}/
POST /api/applications/{id}/generate-documents/
POST /api/applications/{id}/generate-follow-up/
POST /api/applications/{id}/approve-document/
PATCH /api/applications/{id}/documents/{document_id}/
POST /api/applications/{id}/create-gmail-draft/
POST /api/applications/{id}/mark-applied/

GET  /api/mail/messages/
PATCH /api/mail/messages/{id}/
POST /api/mail/sync/
POST /api/mail/messages/{id}/classify/
```

## Mock Behavior

- Campaign runs create realistic mock job postings.
- Job evaluation creates deterministic `JobMatch` entries.
- Application document generation creates German cover letter and email drafts.
- AI-like behavior is routed through `backend/ai_services/providers/mock.py`.
- `backend/ai_services/providers/openai_provider.py` can use OpenAI for job matching only when explicitly configured.
- Gmail draft creation is simulated only.
- Mail sync and classification are mock-based.
- No real job board scraping, Gmail API, email sending, or secrets are used.

## Testing OpenAI Job Matching

OpenAI matching is optional and disabled by default.

1. Install backend requirements after pulling changes:

   ```bash
   cd backend
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Set local `.env` values:

   ```text
   AI_PROVIDER=openai
   OPENAI_API_KEY=your-local-key
   OPENAI_MODEL=gpt-4o-mini
   ```

3. Start the backend and evaluate a job:

   ```bash
   python manage.py runserver
   ```

   Then call `POST /api/jobs/{id}/evaluate/` from the frontend flow or an API client.

Only job matching sends job data to OpenAI, and only when `AI_PROVIDER=openai`.
Document generation, follow-up drafting, and mail classification remain mock-based.

## Demo Data

`python manage.py seed_demo_data` creates:

- TRIOLOGY GmbH / Junior Softwareentwickler Python / Web / 91%
- KOSATEC Computer GmbH / AI Enthusiast / Automation Specialist / 88%
- Beispiel Commerce AG / E-Commerce Developer / Web Operations / 83%
- Stadt Wolfenbüttel / IT-Servicedesk Mitarbeiter*in / 76%
- 2 search campaigns
- 3 email messages
- several applications with different statuses
- status events and draft documents

## Admin

Django Admin is enabled at:

```text
http://127.0.0.1:8000/admin/
```

Create a local admin user with:

```bash
python manage.py createsuperuser
```
