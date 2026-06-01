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

The sidebar uses React Router routes for Übersicht, Suchkampagnen, Gefundene Jobs, Bewerbungen, Mail-Zentrale, Follow-ups, Profil, and Einstellungen. Non-dashboard pages are placeholders for now.

Manual job import is available from the dashboard and `Gefundene Jobs` page. Imported jobs are stored through the backend and immediately evaluated with the deterministic mock matching service.

Creating a simulated Gmail draft remains human-in-the-loop: the frontend opens a document review workflow where generated documents can be edited and explicitly approved before calling the mock Gmail draft endpoint.

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
- `GET /api/mail/messages/`
- `POST /api/jobs/{id}/create-application/`
- `POST /api/applications/{id}/generate-documents/`
- `POST /api/applications/{id}/approve-document/`
- `PATCH /api/applications/{id}/documents/{document_id}/`
- `POST /api/applications/{id}/create-gmail-draft/`
- `POST /api/campaigns/`
- `POST /api/campaigns/{id}/run/`
- `POST /api/mail/sync/`

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
POST /api/applications/{id}/approve-document/
PATCH /api/applications/{id}/documents/{document_id}/
POST /api/applications/{id}/create-gmail-draft/
POST /api/applications/{id}/mark-applied/

GET  /api/mail/messages/
POST /api/mail/sync/
POST /api/mail/messages/{id}/classify/
```

## Mock Behavior

- Campaign runs create realistic mock job postings.
- Job evaluation creates deterministic `JobMatch` entries.
- Application document generation creates German cover letter and email drafts.
- Gmail draft creation is simulated only.
- Mail sync and classification are mock-based.
- No real AI API, job board scraping, Gmail API, email sending, or secrets are used.

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
