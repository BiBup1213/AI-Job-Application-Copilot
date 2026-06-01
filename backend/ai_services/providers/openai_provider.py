import json
import logging

from jobs.models import JobMatch

from .mock import MockAIProvider


logger = logging.getLogger(__name__)


CANDIDATE_PROFILE = {
    "level": "junior/practical developer",
    "skills": [
        "Python",
        "Django",
        "JavaScript",
        "React basics",
        "REST APIs",
        "SQL",
        "Docker/Git basics",
    ],
    "background": [
        "E-Commerce background",
        "automation interest",
        "AI/tooling interest",
        "German-language applications",
    ],
}

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
        # TODO: Replace mock delegation with OpenAI-backed German document drafting.
        # Keep explicit human review and approval before any simulated Gmail draft.
        return self.fallback_provider.generate_application_documents(application)

    def generate_follow_up_document(self, application):
        # TODO: Replace mock delegation with OpenAI-backed German follow-up drafting.
        # Keep the tone short, polite, professional, and non-pushy.
        return self.fallback_provider.generate_follow_up_document(application)

    def classify_email_message(self, email):
        # TODO: Replace mock delegation with OpenAI-backed mail classification.
        # Do not mutate application status automatically; keep user confirmation in the UI.
        return self.fallback_provider.classify_email_message(email)

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def _evaluate_job_with_openai(self, job):
        completion = self._get_client().chat.completions.create(
            model=self.model,
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
                            "candidate_profile": CANDIDATE_PROFILE,
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
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "job_match_evaluation",
                    "strict": True,
                    "schema": JOB_MATCH_SCHEMA,
                },
            },
        )
        content = completion.choices[0].message.content
        if not content:
            raise ValueError("OpenAI response did not include JSON content.")
        return self._validate_job_match_payload(json.loads(content))

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
