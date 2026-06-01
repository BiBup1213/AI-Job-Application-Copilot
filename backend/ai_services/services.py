from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from applications.models import Application, ApplicationDocument, StatusEvent
from jobs.models import JobMatch, JobPosting
from mailcenter.models import EmailMessage


APPLICATION_ANGLE = (
    "Nicht als reiner Junior verkaufen, sondern als praktisch geprägter Entwickler "
    "mit Erfahrung in Webentwicklung, Automatisierung, E-Commerce-Prozessen und "
    "schneller Einarbeitung."
)


def _category_for_score(score):
    if score >= 85:
        return JobMatch.Category.A
    if score >= 75:
        return JobMatch.Category.B
    if score >= 60:
        return JobMatch.Category.C
    return JobMatch.Category.X


def _score_for_job(job):
    known_scores = {
        "TRIOLOGY GmbH": 91,
        "KOSATEC Computer GmbH": 88,
        "Beispiel Commerce AG": 83,
        "Stadt Wolfenbüttel": 76,
    }
    if job.company in known_scores:
        return known_scores[job.company]
    text = " ".join(
        [
            job.company,
            job.title,
            job.description,
            " ".join(job.tags or []),
            " ".join(job.requirements or []),
        ]
    ).lower()
    score = 66
    weights = {
        "python": 11,
        "django": 8,
        "web": 7,
        "automation": 8,
        "automatisierung": 8,
        "e-commerce": 7,
        "ai": 6,
        "ki": 6,
        "support": -4,
        "servicedesk": -5,
    }
    for keyword, weight in weights.items():
        if keyword in text:
            score += weight
    if job.remote_type in ["remote", "hybrid"]:
        score += 3
    return max(0, min(100, score))


def evaluate_job_match(job):
    score = _score_for_job(job)
    strengths = [
        "Gute Überschneidung mit praktischer Webentwicklung.",
        "Automatisierungs- und Prozessdenken lassen sich klar positionieren.",
    ]
    risks = []
    if score < 80:
        risks.append("Einige Anforderungen sollten vor einer Bewerbung manuell geprüft werden.")
    if "servicedesk" in job.title.lower():
        risks.append("Rolle kann stärker supportlastig sein als entwicklungsnah.")
    recommendation = (
        "Bewerben, wenn die Aufgaben genug Entwicklungsanteil enthalten."
        if score >= 75
        else "Nur bewerben, wenn die Stelle strategisch gut passt."
    )
    job_match, _ = JobMatch.objects.update_or_create(
        job=job,
        defaults={
            "score": score,
            "category": _category_for_score(score),
            "strengths": strengths,
            "risks": risks,
            "recommendation": recommendation,
            "application_angle": APPLICATION_ANGLE,
        },
    )
    return job_match


def generate_application_documents(application):
    job = application.job
    match = getattr(job, "match", None) or evaluate_job_match(job)
    next_cover_version = _next_document_version(
        application, ApplicationDocument.DocumentType.COVER_LETTER
    )
    next_email_version = _next_document_version(
        application, ApplicationDocument.DocumentType.EMAIL
    )
    cover_letter = ApplicationDocument.objects.create(
        application=application,
        document_type=ApplicationDocument.DocumentType.COVER_LETTER,
        title=f"Anschreiben {job.company} - {job.title}",
        version=next_cover_version,
        content=(
            f"Sehr geehrtes Recruiting-Team von {job.company},\n\n"
            f"die Position als {job.title} spricht mich an, weil sie praktische "
            "Softwareentwicklung mit klarer Problemlösung verbindet. Ich bringe "
            "Erfahrung in Webentwicklung, Automatisierung und strukturiertem "
            "Arbeiten an digitalen Prozessen mit.\n\n"
            f"Mein Bewerbungswinkel: {match.application_angle}\n\n"
            "Besonders relevant sind meine schnelle Einarbeitung, mein Blick für "
            "verlässliche Abläufe und meine Bereitschaft, Verantwortung für konkrete "
            "Umsetzungsschritte zu übernehmen.\n\n"
            "Mit freundlichen Grüßen\n"
            "Bob"
        ),
    )
    email = ApplicationDocument.objects.create(
        application=application,
        document_type=ApplicationDocument.DocumentType.EMAIL,
        title=f"Bewerbung als {job.title}",
        version=next_email_version,
        content=(
            "Sehr geehrtes Recruiting-Team,\n\n"
            f"anbei erhalten Sie meine Bewerbung für die Position {job.title}. "
            "Ich freue mich besonders auf Aufgaben, bei denen ich Webentwicklung, "
            "Automatisierung und pragmatische Prozessverbesserung verbinden kann.\n\n"
            "Gerne erläutere ich meine Motivation und relevante Projekte in einem "
            "persönlichen Gespräch.\n\n"
            "Mit freundlichen Grüßen\n"
            "Bob"
        ),
    )
    return [cover_letter, email]


def classify_email_message(email):
    subject = email.subject.lower()
    body = email.body.lower()
    text = f"{subject} {body}"
    if any(word in text for word in ["einladung", "gespräch", "interview", "termin"]):
        classification = EmailMessage.Classification.INVITATION
    elif any(word in text for word in ["leider", "absage", "nicht berücksichtigen"]):
        classification = EmailMessage.Classification.REJECTION
    elif any(word in text for word in ["eingegangen", "bestätigung", "erhalten"]):
        classification = EmailMessage.Classification.CONFIRMATION
    elif any(word in text for word in ["frage", "rückfrage", "unterlagen"]):
        classification = EmailMessage.Classification.QUESTION
    elif any(word in text for word in ["bitte", "antwort", "rückmeldung"]):
        classification = EmailMessage.Classification.REQUIRES_ACTION
    else:
        classification = EmailMessage.Classification.UNKNOWN
    email.classification = classification
    email.save(update_fields=["classification"])
    return classification


def suggest_next_actions():
    actions = []
    draft_open = Application.objects.filter(status=Application.Status.DRAFT_OPEN).count()
    follow_up_due = Application.objects.filter(
        follow_up_at__lte=timezone.now(),
        status__in=[Application.Status.APPLIED, Application.Status.FOLLOW_UP_DUE],
    ).count()
    requires_action = EmailMessage.objects.filter(
        classification__in=[
            EmailMessage.Classification.INVITATION,
            EmailMessage.Classification.QUESTION,
            EmailMessage.Classification.REQUIRES_ACTION,
        ]
    ).count()
    if draft_open:
        actions.append(f"{draft_open} Entwurf/Entwürfe prüfen und freigeben.")
    if follow_up_due:
        actions.append(f"{follow_up_due} Bewerbung(en) brauchen ein Follow-up.")
    if requires_action:
        actions.append(f"{requires_action} E-Mail(s) erfordern eine manuelle Aktion.")
    if not actions:
        actions.append("Heute keine dringende Aktion. Neue Kampagne starten oder Jobs bewerten.")
    return actions


def create_mock_jobs_for_campaign(campaign):
    now = timezone.now()
    mock_jobs = [
        {
            "company": "TRIOLOGY GmbH",
            "title": "Junior Softwareentwickler Python / Web",
            "location": "Braunschweig",
            "source": "Mock StepStone",
            "source_url": "https://example.test/jobs/triology-python-web",
            "description": "Entwicklung von Webanwendungen mit Python, Django und APIs.",
            "requirements": ["Python", "Django", "REST APIs", "Git"],
            "nice_to_have": ["Docker", "Automatisierung", "Frontend-Grundlagen"],
            "tags": ["python", "django", "web", "automation"],
            "employment_type": "Vollzeit",
            "remote_type": "hybrid",
            "published_at": now - timedelta(days=1),
        },
        {
            "company": "KOSATEC Computer GmbH",
            "title": "AI Enthusiast / Automation Specialist",
            "location": "Braunschweig",
            "source": "Mock LinkedIn",
            "source_url": "https://example.test/jobs/kosatec-ai-automation",
            "description": "Automatisierung interner Abläufe und Bewertung von KI-Use-Cases.",
            "requirements": ["Automatisierung", "Python", "Prozessanalyse"],
            "nice_to_have": ["E-Commerce", "APIs", "Prompting"],
            "tags": ["ai", "automation", "python", "e-commerce"],
            "employment_type": "Vollzeit",
            "remote_type": "hybrid",
            "published_at": now - timedelta(days=2),
        },
        {
            "company": "Beispiel Commerce AG",
            "title": "E-Commerce Developer / Web Operations",
            "location": campaign.location or "Remote",
            "source": "Mock Indeed",
            "source_url": "https://example.test/jobs/beispiel-commerce-web-ops",
            "description": "Betreuung von Shop-Prozessen, Webentwicklung und Automatisierung.",
            "requirements": ["Webentwicklung", "E-Commerce", "SQL"],
            "nice_to_have": ["Python", "Monitoring", "Schnittstellen"],
            "tags": ["web", "e-commerce", "automation"],
            "employment_type": "Vollzeit",
            "remote_type": "remote" if campaign.remote_allowed else "hybrid",
            "published_at": now - timedelta(days=3),
        },
    ]
    jobs = []
    for payload in mock_jobs:
        job, _ = JobPosting.objects.get_or_create(
            source_url=payload["source_url"],
            defaults=payload,
        )
        evaluate_job_match(job)
        jobs.append(job)
    return jobs


def sync_mock_email_messages():
    now = timezone.now()
    applications = list(Application.objects.select_related("job").all()[:3])
    payloads = [
        {
            "application": applications[0] if applications else None,
            "sender": "recruiting@triology.example",
            "subject": "Bestätigung Ihrer Bewerbung",
            "body": "Vielen Dank, Ihre Bewerbung ist bei uns eingegangen.",
            "received_at": now - timedelta(hours=5),
        },
        {
            "application": applications[1] if len(applications) > 1 else None,
            "sender": "jobs@kosatec.example",
            "subject": "Rückfrage zu Ihren Unterlagen",
            "body": "Wir haben eine Rückfrage zu Ihrem frühestmöglichen Starttermin.",
            "received_at": now - timedelta(days=1),
        },
        {
            "application": applications[2] if len(applications) > 2 else None,
            "sender": "karriere@commerce.example",
            "subject": "Einladung zum Kennenlernen",
            "body": "Wir möchten Sie gerne zu einem ersten Gespräch einladen.",
            "received_at": now - timedelta(days=2),
        },
    ]
    messages = []
    for payload in payloads:
        message, created = EmailMessage.objects.get_or_create(
            sender=payload["sender"],
            subject=payload["subject"],
            defaults=payload,
        )
        if created:
            classify_email_message(message)
        messages.append(message)
    return messages


def dashboard_summary():
    now = timezone.now()
    new_matching_jobs = JobMatch.objects.filter(
        score__gte=75,
        job__applications__isnull=True,
    ).distinct().count()
    open_drafts = Application.objects.filter(
        status__in=[
            Application.Status.DRAFT_OPEN,
            Application.Status.DRAFT_APPROVED,
            Application.Status.GMAIL_DRAFT_CREATED,
        ]
    ).count()
    applied_count = Application.objects.filter(
        status__in=[
            Application.Status.APPLIED,
            Application.Status.RESPONSE_RECEIVED,
            Application.Status.INTERVIEW,
            Application.Status.REJECTED,
            Application.Status.FOLLOW_UP_DUE,
            Application.Status.CLOSED,
        ]
    ).count()
    responses_count = EmailMessage.objects.filter(application__isnull=False).exclude(
        classification=EmailMessage.Classification.UNKNOWN
    ).count()
    followups_due = Application.objects.filter(
        Q(status=Application.Status.FOLLOW_UP_DUE) | Q(follow_up_at__lte=now)
    ).count()

    return {
        "kpis": {
            "new_matching_jobs": new_matching_jobs,
            "open_drafts": open_drafts,
            "applied_count": applied_count,
            "responses_count": responses_count,
            "followups_due": followups_due,
        },
        "jobs_total": JobPosting.objects.count(),
        "applications_total": Application.objects.count(),
        "applications_by_status": dict(
            Application.objects.values_list("status").annotate(count=Count("id"))
        ),
        "emails_requiring_attention": EmailMessage.objects.filter(
            classification__in=[
                EmailMessage.Classification.INVITATION,
                EmailMessage.Classification.QUESTION,
                EmailMessage.Classification.REQUIRES_ACTION,
            ]
        ).count(),
        "top_matches": [
            {
                "job_id": match.job_id,
                "company": match.job.company,
                "title": match.job.title,
                "score": match.score,
                "category": match.category,
            }
            for match in JobMatch.objects.select_related("job").order_by("-score")[:5]
        ],
        "next_actions": suggest_next_actions(),
    }


def _next_document_version(application, document_type):
    latest = (
        application.documents.filter(document_type=document_type)
        .order_by("-version")
        .first()
    )
    return 1 if latest is None else latest.version + 1
