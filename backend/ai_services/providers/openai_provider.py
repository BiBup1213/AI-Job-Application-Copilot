import json
import logging

from applications.models import ApplicationDocument
from ai_services.profile_payload import get_candidate_profile_payload
from jobs.models import JobMatch
from mailcenter.models import EmailMessage

from .mock import MockAIProvider


logger = logging.getLogger(__name__)


class OpenAIProviderError(Exception):
    pass


class OpenAIAPIRequestError(OpenAIProviderError):
    pass


class StructuredOutputParseError(OpenAIProviderError):
    pass


class StructuredOutputValidationError(OpenAIProviderError):
    def __init__(self, field_name, message):
        self.field_name = field_name
        super().__init__(message)


class NoOutputTextError(OpenAIProviderError):
    pass


JOB_MATCH_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "category": {"type": "string", "enum": ["A", "B", "C", "X"]},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "risks": {"type": "array", "items": {"type": "string"}},
        "recommendation": {"type": "string"},
        "application_angle": {"type": "string"},
    },
    "required": [
        "score",
        "category",
        "strengths",
        "risks",
        "recommendation",
        "application_angle",
    ],
}

APPLICATION_DOCUMENTS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "cover_letter": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["title", "content"],
        },
        "email": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["title", "content"],
        },
    },
    "required": ["cover_letter", "email"],
}

FOLLOW_UP_DOCUMENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {"type": "string"},
        "content": {"type": "string"},
    },
    "required": ["title", "content"],
}

EMAIL_CLASSIFICATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "classification": {
            "type": "string",
            "enum": [
                "confirmation",
                "rejection",
                "invitation",
                "question",
                "follow_up",
                "unknown",
            ],
        },
        "requires_action": {"type": "boolean"},
    },
    "required": ["classification", "requires_action"],
}

PROFILE_SUGGESTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "full_name": {"type": "string"},
        "email": {"type": "string"},
        "location": {"type": "string"},
        "target_roles": {"type": "array", "items": {"type": "string"}},
        "preferred_locations": {"type": "array", "items": {"type": "string"}},
        "remote_preference": {"type": "string"},
        "salary_expectation": {"type": "string"},
        "availability": {"type": "string"},
        "skills": {"type": "array", "items": {"type": "string"}},
        "tech_stack": {"type": "array", "items": {"type": "string"}},
        "projects": {"type": "array", "items": {"type": "string"}},
        "experience_summary": {"type": "string"},
        "education_summary": {"type": "string"},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "no_gos": {"type": "array", "items": {"type": "string"}},
        "application_tone": {"type": "string"},
        "extra_context": {"type": "string"},
        "confidence_notes": {"type": "array", "items": {"type": "string"}},
        "missing_information": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "full_name",
        "email",
        "location",
        "target_roles",
        "preferred_locations",
        "remote_preference",
        "salary_expectation",
        "availability",
        "skills",
        "tech_stack",
        "projects",
        "experience_summary",
        "education_summary",
        "strengths",
        "no_gos",
        "application_tone",
        "extra_context",
        "confidence_notes",
        "missing_information",
    ],
}


class OpenAIProvider:
    def __init__(self, api_key, model="", fallback_provider=None):
        self.api_key = api_key
        self.model = model
        self.fallback_provider = fallback_provider or MockAIProvider()
        self._client = None

    def evaluate_job_match(self, job):
        if not self.model:
            logger.warning("OPENAI_MODEL is missing; falling back to mock job matching.")
            return self.fallback_provider.evaluate_job_match(job)

        try:
            payload = self._evaluate_job_with_openai(job)
            job_match, _ = JobMatch.objects.update_or_create(
                job=job,
                defaults=payload,
            )
            return job_match
        except Exception:
            logger.warning(
                "OpenAI job matching failed; falling back to mock provider.",
                exc_info=True,
            )
            return self.fallback_provider.evaluate_job_match(job)

    def generate_application_documents(self, application):
        if not self.model:
            logger.warning(
                "OPENAI_MODEL is missing; falling back to mock application documents."
            )
            return self.fallback_provider.generate_application_documents(application)

        try:
            payload = self._generate_application_documents_with_openai(application)
            cover_letter_payload = payload["cover_letter"]
            email_payload = payload["email"]
            cover_letter = ApplicationDocument.objects.create(
                application=application,
                document_type=ApplicationDocument.DocumentType.COVER_LETTER,
                title=cover_letter_payload["title"],
                content=cover_letter_payload["content"],
                version=self._next_document_version(
                    application, ApplicationDocument.DocumentType.COVER_LETTER
                ),
            )
            email = ApplicationDocument.objects.create(
                application=application,
                document_type=ApplicationDocument.DocumentType.EMAIL,
                title=email_payload["title"],
                content=email_payload["content"],
                version=self._next_document_version(
                    application, ApplicationDocument.DocumentType.EMAIL
                ),
            )
            return [cover_letter, email]
        except Exception:
            logger.warning(
                "OpenAI application document generation failed; falling back to mock provider.",
                exc_info=True,
            )
            return self.fallback_provider.generate_application_documents(application)

    def generate_follow_up_document(self, application):
        if not self.model:
            logger.warning("OPENAI_MODEL is missing; falling back to mock follow-up draft.")
            return self.fallback_provider.generate_follow_up_document(application)

        try:
            payload = self._generate_follow_up_document_with_openai(application)
            return ApplicationDocument.objects.create(
                application=application,
                document_type=ApplicationDocument.DocumentType.FOLLOW_UP,
                title=payload["title"],
                content=payload["content"],
                version=self._next_document_version(
                    application, ApplicationDocument.DocumentType.FOLLOW_UP
                ),
            )
        except Exception:
            logger.warning(
                "OpenAI follow-up document generation failed; falling back to mock provider.",
                exc_info=True,
            )
            return self.fallback_provider.generate_follow_up_document(application)

    def classify_email_message(self, email):
        if not self.model:
            logger.warning("OPENAI_MODEL is missing; falling back to mock mail classification.")
            return self.fallback_provider.classify_email_message(email)

        try:
            payload = self._classify_email_with_openai(email)
            email.classification = payload["classification"]
            email.save(update_fields=["classification"])
            return email.classification
        except Exception:
            logger.warning(
                "OpenAI mail classification failed; falling back to mock provider.",
                exc_info=True,
            )
            return self.fallback_provider.classify_email_message(email)

    def suggest_profile_from_documents(self, profile, documents):
        if not self.model:
            logger.warning("OPENAI_MODEL is missing; falling back to mock profile suggestions.")
            return self._fallback_profile_suggestion(
                profile,
                documents,
                "OPENAI_MODEL missing",
            )

        logger.debug(
            "OpenAI profile suggestion requested with model=%s, documents=%s, source_text_length=%s",
            self.model,
            len(documents),
            self._source_text_length(documents),
        )

        try:
            suggestion = self._suggest_profile_from_documents_with_openai(profile, documents)
            suggestion["_meta"] = self._suggestion_meta("openai", documents)
            return suggestion
        except OpenAIAPIRequestError as exc:
            reason = str(exc)
        except NoOutputTextError as exc:
            reason = str(exc)
        except StructuredOutputParseError as exc:
            reason = str(exc)
        except StructuredOutputValidationError as exc:
            reason = f"Structured output validation failed: {exc.field_name}"
        except Exception as exc:
            reason = f"OpenAI profile suggestion error: {exc.__class__.__name__}"
            logger.warning(
                "OpenAI profile suggestion failed with unexpected error; falling back to mock provider.",
                exc_info=True,
            )
            return self._fallback_profile_suggestion(profile, documents, reason)

        logger.warning(
            "OpenAI profile suggestion failed; falling back to mock provider. reason=%s",
            reason,
        )
        return self._fallback_profile_suggestion(profile, documents, reason)

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def _evaluate_job_with_openai(self, job):
        content = self._create_structured_json(
            schema_name="job_match_evaluation",
            schema=JOB_MATCH_SCHEMA,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Du bewertest Job-Matches für einen Bewerbungs-Copilot. "
                        "Antworte ausschließlich als JSON gemäß Schema. "
                        "Alle Texte müssen auf Deutsch sein. Bewerte realistisch, "
                        "konservativ und passend für einen praktischen Junior-Entwickler."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "candidate_profile": self._candidate_profile_payload(),
                            "job": self._job_payload(job),
                            "category_rules": {
                                "A": "sehr passend, hohe Priorität",
                                "B": "passend, bewerben wenn Aufgaben stimmen",
                                "C": "bedingt passend, manuell sorgfältig prüfen",
                                "X": "nicht passend oder klar zu riskant",
                            },
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        )
        return self._validate_job_match_payload(self._parse_structured_json(content))

    def _generate_application_documents_with_openai(self, application):
        job = application.job
        match = getattr(job, "match", None)
        content = self._create_structured_json(
            schema_name="application_documents",
            schema=APPLICATION_DOCUMENTS_SCHEMA,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Du erstellst Bewerbungsunterlagen auf Deutsch. "
                        "Antworte ausschließlich als JSON gemäß Schema. "
                        "Schreibe professionell, prägnant und konkret zur Stelle. "
                        "Erfinde keine Abschlüsse, Arbeitgeber, Zertifikate, Projekte "
                        "oder Berufserfahrung. Keine übertriebenen Behauptungen. "
                        "Die Texte sind Entwürfe für menschliche Prüfung."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "candidate_profile": self._candidate_profile_payload(),
                            "job": self._job_payload(job),
                            "match": self._match_payload(match),
                            "requested_documents": ["cover_letter", "email"],
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        )
        return self._validate_application_documents_payload(self._parse_structured_json(content))

    def _generate_follow_up_document_with_openai(self, application):
        job = application.job
        content = self._create_structured_json(
            schema_name="follow_up_document",
            schema=FOLLOW_UP_DOCUMENT_SCHEMA,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Du erstellst einen kurzen Follow-up-Entwurf auf Deutsch. "
                        "Antworte ausschließlich als JSON gemäß Schema. "
                        "Der Text soll professionell, freundlich, knapp und nicht "
                        "bettelnd sein. Beziehe dich auf die Bewerbung und bitte um "
                        "einen kurzen Zwischenstand. Erfinde keine Fakten."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "candidate_profile": self._candidate_profile_payload(),
                            "job": self._job_payload(job),
                            "application": {
                                "status": application.status,
                                "applied_at": application.applied_at.isoformat()
                                if application.applied_at
                                else None,
                                "follow_up_at": application.follow_up_at.isoformat()
                                if application.follow_up_at
                                else None,
                            },
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        )
        return self._validate_document_payload(self._parse_structured_json(content), "follow_up")

    def _classify_email_with_openai(self, email):
        content = self._create_structured_json(
            schema_name="email_classification",
            schema=EMAIL_CLASSIFICATION_SCHEMA,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Du klassifizierst E-Mails für einen Bewerbungs-Copilot. "
                        "Antworte ausschließlich als JSON gemäß Schema. "
                        "Nutze genau eine der erlaubten Klassifizierungen. "
                        "Setze requires_action auf true, wenn die Person manuell "
                        "reagieren oder die Bewerbung prüfen sollte. Ändere keine "
                        "Bewerbungsstatus automatisch."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "sender": email.sender,
                            "subject": email.subject,
                            "body": email.body,
                            "classification_rules": {
                                "confirmation": "Eingangs- oder Bewerbungsbestätigung ohne weitere Aktion.",
                                "rejection": "Absage oder klare Nichtberücksichtigung.",
                                "invitation": "Einladung zu Gespräch, Interview, Termin oder Kennenlernen.",
                                "question": "Rückfrage, Bitte um Angaben oder fehlende Unterlagen.",
                                "follow_up": "Zwischenstand, Nachfassen oder Follow-up-Kontext.",
                                "unknown": "Nicht eindeutig einer Bewerbungsantwort zuordenbar.",
                            },
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        )
        return self._validate_email_classification_payload(self._parse_structured_json(content))

    def _suggest_profile_from_documents_with_openai(self, profile, documents):
        content = self._create_structured_json(
            schema_name="candidate_profile_suggestion",
            schema=PROFILE_SUGGESTION_SCHEMA,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Du analysierst Bewerbungsunterlagen und schlägst Ergänzungen "
                        "für ein Kandidatenprofil vor. Antworte ausschließlich als JSON "
                        "gemäß Schema. Schreibe auf Deutsch, wo es sinnvoll ist. "
                        "Erfinde keine Fakten, Abschlüsse, Arbeitgeber, Zertifikate, "
                        "Erfahrung oder Präferenzen. Unsichere Informationen gehören in "
                        "confidence_notes oder missing_information. Leere Felder sind erlaubt. "
                        "Achte besonders auf Kontaktbereiche, Seitenleisten, Kopfzeilen, "
                        "mehrspaltige Layouts und uneinheitliche Reihenfolge im extrahierten "
                        "CV-Text. Ausbildung und Berufserfahrung müssen extrahiert werden, "
                        "wenn sie im Dokument belegt sind."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "current_profile": self._profile_payload(profile),
                            "documents": self._documents_payload(documents),
                            "instructions": (
                                "Extrahiere strukturierte Kandidatenprofil-Daten aus CVs, "
                                "Zertifikaten, Referenzen und Bewerbungsdokumenten. Suche nach "
                                "Name, E-Mail, Telefonnummer, Standort/Adresse, Zielrollen, "
                                "Skills, Tech Stack, Projekten, Berufserfahrung, Ausbildung, "
                                "Stärken, Bewerbungston und expliziten No-Gos. Telefonnummern "
                                "kommen in extra_context. CVs können mehrspaltig sein; nutze den "
                                "gesamten extrahierten Text auch bei ungewöhnlicher Reihenfolge. "
                                "Erzeuge Vorschläge, die ein Mensch prüfen und übernehmen kann. "
                                "Keine automatischen Überschreibungen annehmen. Erfinde keine "
                                "nicht belegten Fakten; fehlende Informationen leer lassen oder "
                                "in missing_information nennen."
                            ),
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        )
        return self._validate_profile_suggestion_payload(self._parse_structured_json(content))

    def _fallback_profile_suggestion(self, profile, documents, reason):
        logger.debug(
            "Using mock fallback for profile suggestions. reason=%s, source_text_length=%s",
            reason,
            self._source_text_length(documents),
        )
        self.fallback_provider.fallback_reason = reason
        return self.fallback_provider.suggest_profile_from_documents(profile, documents)

    def _candidate_profile_payload(self):
        return get_candidate_profile_payload()

    def _create_structured_json(self, schema_name, schema, messages):
        logger.debug(
            "Calling OpenAI structured output. model=%s, schema=%s",
            self.model,
            schema_name,
        )
        try:
            completion = self._get_client().chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_name,
                        "strict": True,
                        "schema": schema,
                    },
                },
            )
        except Exception as exc:
            logger.warning(
                "OpenAI structured output request failed. schema=%s, exception=%s",
                schema_name,
                exc.__class__.__name__,
            )
            raise OpenAIAPIRequestError(self._safe_api_error(exc)) from exc

        try:
            message = completion.choices[0].message
        except (AttributeError, IndexError, TypeError) as exc:
            raise NoOutputTextError("No output text returned") from exc

        refusal = getattr(message, "refusal", None)
        if refusal:
            raise NoOutputTextError("No output text returned: model refusal")

        content = getattr(message, "content", None)
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else getattr(part, "text", "")
                for part in content
            )
        if not isinstance(content, str) or not content.strip():
            raise NoOutputTextError("No output text returned")
        return content

    def _parse_structured_json(self, content):
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise StructuredOutputParseError(
                f"Structured output parse error: {self._safe_exception_detail(exc)}"
            ) from exc

    def _safe_exception_detail(self, exc):
        message = str(exc).replace("\n", " ").strip()
        if self.api_key:
            message = message.replace(self.api_key, "[redacted]")
        if len(message) > 180:
            message = message[:177] + "..."
        return f"{exc.__class__.__name__}: {message}" if message else exc.__class__.__name__

    def _safe_api_error(self, exc):
        return f"OpenAI API error: {self._safe_exception_detail(exc)}"

    def _source_text_length(self, documents):
        return sum(len((document.extracted_text or "").strip()) for document in documents)

    def _job_payload(self, job):
        return {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "source": job.source,
            "description": job.description,
            "requirements": job.requirements or [],
            "nice_to_have": job.nice_to_have or [],
            "tags": job.tags or [],
        }

    def _match_payload(self, match):
        if not match:
            return None
        return {
            "score": match.score,
            "category": match.category,
            "strengths": match.strengths or [],
            "risks": match.risks or [],
            "recommendation": match.recommendation,
            "application_angle": match.application_angle,
        }

    def _profile_payload(self, profile):
        if not profile:
            return {}
        return {
            "full_name": profile.full_name,
            "email": profile.email,
            "location": profile.location,
            "target_roles": profile.target_roles or [],
            "preferred_locations": profile.preferred_locations or [],
            "remote_preference": profile.remote_preference,
            "salary_expectation": profile.salary_expectation,
            "availability": profile.availability,
            "skills": profile.skills or [],
            "tech_stack": profile.tech_stack or [],
            "projects": profile.projects or [],
            "experience_summary": profile.experience_summary,
            "education_summary": profile.education_summary,
            "strengths": profile.strengths or [],
            "no_gos": profile.no_gos or [],
            "application_tone": profile.application_tone,
            "extra_context": profile.extra_context,
        }

    def _documents_payload(self, documents):
        payload = []
        for document in documents:
            text = (document.extracted_text or "").strip()
            payload.append(
                {
                    "id": document.id,
                    "title": document.title,
                    "document_type": document.document_type,
                    "original_filename": document.original_filename,
                    "extraction_status": document.extraction_status,
                    "extraction_error": document.extraction_error,
                    "notes": document.notes,
                    "has_extracted_text": bool(text),
                    "extracted_text": text[:8000],
                }
            )
        return payload

    def _suggestion_meta(self, provider_used, documents, fallback_reason=""):
        return {
            "provider_used": provider_used,
            "fallback_used": bool(fallback_reason),
            "fallback_reason": fallback_reason,
            "source_text_length": self._source_text_length(documents),
            "document_count": len(documents),
        }

    def _validate_job_match_payload(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("OpenAI job match response is not an object.")

        score = payload.get("score")
        if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
            raise ValueError("OpenAI job match score must be an integer from 0 to 100.")

        category = payload.get("category")
        if category not in {choice.value for choice in JobMatch.Category}:
            raise ValueError("OpenAI job match category is invalid.")

        strengths = self._validate_string_list(payload.get("strengths"), "strengths")
        risks = self._validate_string_list(payload.get("risks"), "risks")
        recommendation = self._validate_string(payload.get("recommendation"), "recommendation")
        application_angle = self._validate_string(
            payload.get("application_angle"), "application_angle"
        )

        return {
            "score": score,
            "category": category,
            "strengths": strengths,
            "risks": risks,
            "recommendation": recommendation,
            "application_angle": application_angle,
        }

    def _validate_string_list(self, value, field_name):
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            raise ValueError(f"OpenAI job match {field_name} must be a string array.")
        return [item.strip() for item in value]

    def _validate_string(self, value, field_name):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"OpenAI job match {field_name} must be a non-empty string.")
        return value.strip()

    def _validate_application_documents_payload(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("OpenAI application document response is not an object.")
        return {
            "cover_letter": self._validate_document_payload(
                payload.get("cover_letter"), "cover_letter"
            ),
            "email": self._validate_document_payload(payload.get("email"), "email"),
        }

    def _validate_document_payload(self, payload, field_name):
        if not isinstance(payload, dict):
            raise ValueError(f"OpenAI {field_name} response is not an object.")
        return {
            "title": self._validate_document_string(payload.get("title"), f"{field_name}.title"),
            "content": self._validate_document_string(
                payload.get("content"), f"{field_name}.content"
            ),
        }

    def _validate_document_string(self, value, field_name):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"OpenAI document {field_name} must be a non-empty string.")
        return value.strip()

    def _validate_email_classification_payload(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("OpenAI mail classification response is not an object.")

        classification = payload.get("classification")
        allowed_classifications = {
            EmailMessage.Classification.CONFIRMATION,
            EmailMessage.Classification.REJECTION,
            EmailMessage.Classification.INVITATION,
            EmailMessage.Classification.QUESTION,
            EmailMessage.Classification.FOLLOW_UP,
            EmailMessage.Classification.UNKNOWN,
        }
        if classification not in allowed_classifications:
            raise ValueError("OpenAI mail classification value is invalid.")

        requires_action = payload.get("requires_action")
        if not isinstance(requires_action, bool):
            raise ValueError("OpenAI mail requires_action must be a boolean.")

        return {
            "classification": classification,
            "requires_action": requires_action,
        }

    def _validate_profile_suggestion_payload(self, payload):
        if not isinstance(payload, dict):
            raise StructuredOutputValidationError(
                "root",
                "OpenAI profile suggestion response is not an object.",
            )

        string_fields = [
            "full_name",
            "email",
            "location",
            "remote_preference",
            "salary_expectation",
            "availability",
            "experience_summary",
            "education_summary",
            "application_tone",
            "extra_context",
        ]
        list_fields = [
            "target_roles",
            "preferred_locations",
            "skills",
            "tech_stack",
            "projects",
            "strengths",
            "no_gos",
            "confidence_notes",
            "missing_information",
        ]
        cleaned = {}
        for field in string_fields:
            cleaned[field] = self._profile_string_value(payload, field)
        for field in list_fields:
            cleaned[field] = self._profile_string_list(payload, field)
        return cleaned

    def _profile_string_value(self, payload, field):
        value = payload.get(field, "")
        if value is None:
            return ""
        if not isinstance(value, str):
            raise StructuredOutputValidationError(
                field,
                f"OpenAI profile suggestion {field} must be a string.",
            )
        return value.strip()

    def _profile_string_list(self, payload, field):
        value = payload.get(field, [])
        if value is None:
            return []
        if not isinstance(value, list):
            raise StructuredOutputValidationError(
                field,
                f"OpenAI profile suggestion {field} must be a string array.",
            )
        cleaned = []
        for item in value:
            if item is None:
                continue
            if not isinstance(item, str):
                raise StructuredOutputValidationError(
                    field,
                    f"OpenAI profile suggestion {field} must be a string array.",
                )
            stripped = item.strip()
            if stripped:
                cleaned.append(stripped)
        return cleaned

    def _next_document_version(self, application, document_type):
        latest = (
            application.documents.filter(document_type=document_type)
            .order_by("-version")
            .first()
        )
        return 1 if latest is None else latest.version + 1
