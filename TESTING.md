# Manual MVP Test Checklist

Use this checklist before adding real Gmail, scraping, or LLM integrations.

## Setup

1. Start the backend:

   ```bash
   cd backend
   source .venv/bin/activate
   python manage.py migrate
   python manage.py seed_demo_data
   python manage.py runserver
   ```

2. Start the frontend:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Open `http://localhost:5173/`.

## Dashboard Smoke Test

- Dashboard loads without a backend error state.
- KPI cards show backend-owned counts.
- Job ranking shows match scores, not `0%` for seeded or campaign-created jobs.
- Pipeline cards open application detail pages.
- Heute wichtig rows navigate to Bewerbungen, Mail-Zentrale, and Follow-ups.

## Manual Job Import

- Open `Gefundene Jobs` or use `Stelle manuell hinzufügen` on the dashboard.
- Try submitting without Firma, Jobtitel, or Stellenbeschreibung and verify validation.
- Add a real-looking job posting.
- Verify the new job appears with a match score.
- Create an application from the imported job.

## Campaign Mock Search

- Create a new search campaign.
- Select sources with checkboxes.
- Submit and verify mock jobs are created and evaluated.
- Confirm no real scraping is called.

## Application Document Review

- Click `Bewerbung erstellen` from a job.
- Verify the review UI opens with Anschreiben and E-Mail.
- Edit a document and save it.
- Verify approval resets after editing an approved document.
- Click `Entwurf freigeben`.

## Simulated Gmail Draft

- Try `Gmail-Entwurf erstellen` before approving the E-Mail document.
- Verify the UI asks for explicit approval first.
- Approve the E-Mail document.
- Create the simulated Gmail draft.
- Verify no real Gmail API call or email sending happens.

## Applications Page

- Open `/bewerbungen`.
- Test each status filter.
- Open an application detail page.
- Edit notes and reload to verify persistence.
- Set a follow-up date and reload to verify persistence.
- Mark an application as applied and verify status/events.

## Mail-Zentrale

- Open `/mail`.
- Click `Synchronisieren`.
- Test mail filters.
- Open a mail detail modal.
- Click `Neu klassifizieren`.
- Link the mail to an application.
- Use `Status aktualisieren` and verify the linked application status changes only after confirmation.
- Confirm `Antwortentwurf erstellen` shows the placeholder notice.

## Follow-ups

- Open `/follow-ups`.
- Verify due, planned, without-date, and done filters.
- Set a follow-up date and reload.
- Generate a follow-up draft.
- Edit and save the follow-up draft.
- Approve the follow-up draft.
- Mark follow-up as done and verify it is no longer due.

## Persistence After Reload

- Reload the browser after each major workflow.
- Confirm jobs, applications, documents, approvals, mail links, notes, statuses, and follow-up dates persist in SQLite.
