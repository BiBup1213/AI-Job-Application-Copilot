import json
import logging

from applications.models import ApplicationDocument
from ai_services.profile_payload import get_candidate_profile_payload
from jobs.models import JobMatch
from mailcenter.models import EmailMessage

from .mock import MockAIProvider


logger = logging.getLogger(__name__)


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
        return self._validate_job_match_payload(json.loads(content))

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
        return self._validate_application_documents_payload(json.loads(content))

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
        return self._validate_document_payload(json.loads(content), "follow_up")

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
        return self._validate_email_classification_payload(json.loads(content))

    def _candidate_profile_payload(self):
        return get_candidate_profile_payload()

    def _create_structured_json(self, schema_name, schema, messages):
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
        content = completion.choices[0].message.content
        if not content:
            raise ValueError("OpenAI response did not include JSON content.")
        return content

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

    def _next_document_version(self, application, document_type):
        latest = (
            application.documents.filter(document_type=document_type)
            .order_by("-version")
            .first()
        )
        return 1 if latest is None else latest.version + 1
