from datetime import timedelta
import logging

from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone

from applications.models import Application
from ai_services.models import CandidateProfile
from ai_services.providers.mock import APPLICATION_ANGLE, MockAIProvider
from ai_services.providers.openai_provider import OpenAIProvider
from jobs.models import JobMatch, JobPosting
from mailcenter.models import EmailMessage


logger = logging.getLogger(__name__)
_provider = None
_mock_provider = None


def get_mock_provider():
    global _mock_provider
    if _mock_provider is None:
        _mock_provider = MockAIProvider()
    return _mock_provider


def get_provider():
    global _provider
    if _provider is not None:
        return _provider

    provider_name = getattr(settings, "AI_PROVIDER", "mock").strip().lower()
    if provider_name == "mock":
        _provider = get_mock_provider()
        _provider.fallback_reason = ""
        return _provider

    if provider_name == "openai":
        api_key = getattr(settings, "OPENAI_API_KEY", "")
        if not api_key:
            logger.warning(
                "AI_PROVIDER=openai configured but OPENAI_API_KEY is missing; "
                "falling back to mock provider."
            )
            _provider = _mock_provider_with_reason("missing API key")
            return _provider
        try:
            _provider = OpenAIProvider(
                api_key=api_key,
                model=getattr(settings, "OPENAI_MODEL", ""),
                fallback_provider=get_mock_provider(),
            )
            return _provider
        except Exception:
            logger.warning(
                "OpenAI provider initialization failed; falling back to mock provider.",
                exc_info=True,
            )
            _provider = _mock_provider_with_reason("OpenAI provider initialization failed")
            return _provider

    logger.warning(
        "Unsupported AI_PROVIDER '%s'; falling back to mock provider.",
        provider_name,
    )
    _provider = _mock_provider_with_reason(f"unsupported AI_PROVIDER '{provider_name}'")
    return _provider


def _mock_provider_with_reason(reason):
    provider = get_mock_provider()
    provider.fallback_reason = reason
    return provider


def _call_provider(method_name, *args):
    provider = get_provider()
    try:
        return getattr(provider, method_name)(*args)
    except Exception:
        if provider is get_mock_provider():
            raise
        logger.warning(
            "Configured AI provider failed during %s; falling back to mock provider.",
            method_name,
            exc_info=True,
        )
        fallback_provider = _mock_provider_with_reason(f"{method_name} provider error")
        return getattr(fallback_provider, method_name)(*args)


def evaluate_job_match(job):
    return _call_provider("evaluate_job_match", job)


def generate_application_documents(application):
    return _call_provider("generate_application_documents", application)


def generate_follow_up_document(application):
    return _call_provider("generate_follow_up_document", application)


def classify_email_message(email):
    return _call_provider("classify_email_message", email)


def suggest_profile_from_documents(profile, documents):
    return _call_provider("suggest_profile_from_documents", profile, documents)


def apply_profile_suggestion(suggestion):
    profile = suggestion.profile or CandidateProfile.objects.first() or CandidateProfile.objects.create()
    data = suggestion.suggested_data or {}
    list_fields = [
        "target_roles",
        "preferred_locations",
        "skills",
        "tech_stack",
        "projects",
        "strengths",
        "no_gos",
    ]
    scalar_fields = [
        "full_name",
        "email",
        "location",
        "remote_preference",
        "salary_expectation",
        "availability",
        "application_tone",
    ]
    append_text_fields = ["experience_summary", "education_summary", "extra_context"]

    for field in list_fields:
        merged = _merge_list(getattr(profile, field, []) or [], data.get(field, []))
        setattr(profile, field, merged)

    for field in scalar_fields:
        current = getattr(profile, field, "")
        suggestion_value = data.get(field, "")
        if not current and isinstance(suggestion_value, str) and suggestion_value.strip():
            setattr(profile, field, suggestion_value.strip())

    for field in append_text_fields:
        current = getattr(profile, field, "")
        suggestion_value = data.get(field, "")
        if isinstance(suggestion_value, str) and suggestion_value.strip():
            setattr(profile, field, _append_unique_text(current, suggestion_value.strip()))

    profile.save()
    suggestion.profile = profile
    suggestion.status = suggestion.Status.APPLIED
    suggestion.applied_at = timezone.now()
    suggestion.save(update_fields=["profile", "status", "applied_at", "updated_at"])
    return profile


def _merge_list(current, suggested):
    values = []
    seen = set()
    for value in [*current, *suggested]:
        if not isinstance(value, str):
            value = str(value)
        normalized = value.strip()
        key = normalized.lower()
        if normalized and key not in seen:
            values.append(normalized)
            seen.add(key)
    return values


def _append_unique_text(current, suggestion_value):
    current = current or ""
    if suggestion_value.lower() in current.lower():
        return current
    if not current.strip():
        return suggestion_value
    return f"{current.rstrip()}\n\n{suggestion_value}"


def suggest_next_actions():
    actions = []
    draft_open = Application.objects.filter(status=Application.Status.DRAFT_OPEN).count()
    follow_up_due = _followups_due_queryset().count()
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
    followups_due = _followups_due_queryset(now).count()

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


def _followups_due_queryset(now=None):
    now = now or timezone.now()
    response_classifications = [
        EmailMessage.Classification.INVITATION,
        EmailMessage.Classification.QUESTION,
        EmailMessage.Classification.REJECTION,
        EmailMessage.Classification.FOLLOW_UP,
        EmailMessage.Classification.REQUIRES_ACTION,
    ]
    active_applications = Application.objects.exclude(
        status__in=[Application.Status.CLOSED, Application.Status.REJECTED]
    )
    scheduled_or_marked = active_applications.filter(
        Q(status=Application.Status.FOLLOW_UP_DUE) | Q(follow_up_at__lte=now)
    ).values("id")
    stale_applied = (
        active_applications.filter(
            status=Application.Status.APPLIED,
            follow_up_at__isnull=True,
            applied_at__lte=now - timedelta(days=7),
        )
        .exclude(emails__classification__in=response_classifications)
        .values("id")
    )
    return active_applications.filter(
        Q(id__in=scheduled_or_marked) | Q(id__in=stale_applied)
    ).distinct()
