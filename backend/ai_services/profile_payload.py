from .models import CandidateDocument, CandidateProfile


MAX_DOCUMENT_CONTEXT_CHARS = 12000
MAX_SINGLE_DOCUMENT_CHARS = 4000


FALLBACK_CANDIDATE_PROFILE = {
    "full_name": "",
    "email": "",
    "location": "",
    "target_roles": ["Junior Softwareentwickler", "Web Developer"],
    "preferred_locations": ["Deutschland"],
    "remote_preference": "Remote oder Hybrid",
    "salary_expectation": "",
    "availability": "",
    "skills": ["Python", "Django", "JavaScript", "REST APIs", "SQL"],
    "tech_stack": ["Python", "Django", "React basics", "Docker/Git basics"],
    "projects": ["Webentwicklung, Automatisierung und E-Commerce-Prozesse"],
    "experience_summary": "Praktisch geprägter Junior-Entwickler mit Webentwicklungs- und Automatisierungsinteresse.",
    "education_summary": "",
    "strengths": [
        "schnelle Einarbeitung",
        "pragmatische Umsetzung",
        "Interesse an AI- und Tooling-Themen",
    ],
    "no_gos": [],
    "application_tone": "professionell, klar und praxisnah",
    "extra_context": "Deutschsprachige Bewerbungen.",
    "documents_context": [],
}


def get_candidate_profile_payload():
    profile = CandidateProfile.objects.first()
    if profile is None:
        return FALLBACK_CANDIDATE_PROFILE.copy()
    return {
        "full_name": profile.full_name,
        "email": profile.email,
        "location": profile.location,
        "target_roles": _list_or_empty(profile.target_roles),
        "preferred_locations": _list_or_empty(profile.preferred_locations),
        "remote_preference": profile.remote_preference,
        "salary_expectation": profile.salary_expectation,
        "availability": profile.availability,
        "skills": _list_or_empty(profile.skills),
        "tech_stack": _list_or_empty(profile.tech_stack),
        "projects": _list_or_empty(profile.projects),
        "experience_summary": profile.experience_summary,
        "education_summary": profile.education_summary,
        "strengths": _list_or_empty(profile.strengths),
        "no_gos": _list_or_empty(profile.no_gos),
        "application_tone": profile.application_tone,
        "extra_context": profile.extra_context,
        "documents_context": _document_context(profile),
    }


def candidate_display_name():
    payload = get_candidate_profile_payload()
    return payload.get("full_name") or "Max Beispiel"


def _list_or_empty(value):
    return value if isinstance(value, list) else []


def _document_context(profile):
    documents = (
        CandidateDocument.objects.filter(
            profile=profile,
            use_for_ai_context=True,
            extraction_status=CandidateDocument.ExtractionStatus.SUCCESS,
        )
        .exclude(extracted_text="")
        .order_by("-updated_at", "-id")
    )
    context = []
    total_chars = 0
    for document in documents:
        if total_chars >= MAX_DOCUMENT_CONTEXT_CHARS:
            break
        remaining = MAX_DOCUMENT_CONTEXT_CHARS - total_chars
        text = document.extracted_text.strip()
        text = text[: min(MAX_SINGLE_DOCUMENT_CHARS, remaining)]
        if not text:
            continue
        context.append(
            {
                "title": document.title,
                "document_type": document.document_type,
                "text": text,
            }
        )
        total_chars += len(text)
    return context
