from types import SimpleNamespace

from django.conf import settings
from django.core.management.base import BaseCommand

from ai_services.models import CandidateProfile
from ai_services.services import get_provider, suggest_profile_from_documents


SAMPLE_CV_TEXT = """
Max Beispiel
Braunschweig
max.beispiel@example.com

Profil
Praktisch geprägter Junior-Entwickler mit Erfahrung in Python, Django,
JavaScript, React-Grundlagen, REST APIs, SQL, Docker und Git. Interesse an
Automatisierung, KI-Tooling und E-Commerce-Prozessen.

Berufserfahrung
2024 - heute: Web- und Automatisierungsprojekte im E-Commerce-Umfeld,
API-Integrationen, kleine Django-Anwendungen und Prozessverbesserungen.

Ausbildung
2021 - 2024: Fachinformatiker Anwendungsentwicklung, Beispiel Berufsschule.

Stärken
Schnelle Einarbeitung, strukturierte Umsetzung, pragmatische Problemlösung.
"""


class Command(BaseCommand):
    help = "Test the configured AI provider with a sample profile suggestion request."

    def handle(self, *args, **options):
        provider = get_provider()
        api_key_configured = bool(getattr(settings, "OPENAI_API_KEY", ""))
        model = getattr(settings, "OPENAI_MODEL", "")

        self.stdout.write(f"AI_PROVIDER: {getattr(settings, 'AI_PROVIDER', 'mock')}")
        self.stdout.write(f"Provider class: {provider.__class__.__name__}")
        self.stdout.write(f"OPENAI_API_KEY configured: {'yes' if api_key_configured else 'no'}")
        self.stdout.write(f"OPENAI_MODEL: {model or '<missing>'}")

        profile = CandidateProfile.objects.first() or CandidateProfile(
            full_name="",
            email="",
            location="",
        )
        document = SimpleNamespace(
            id="sample",
            title="Sample CV",
            document_type="cv",
            original_filename="sample-cv.txt",
            extraction_status="success",
            extraction_error="",
            notes="Synthetic management-command sample.",
            extracted_text=SAMPLE_CV_TEXT,
        )

        suggestion = suggest_profile_from_documents(profile, [document])
        meta = suggestion.get("_meta", {})

        self.stdout.write("")
        self.stdout.write("Profile suggestion result")
        self.stdout.write(f"provider_used: {meta.get('provider_used', '<missing>')}")
        self.stdout.write(f"fallback_used: {meta.get('fallback_used', False)}")
        self.stdout.write(f"fallback_reason: {meta.get('fallback_reason', '')}")
        self.stdout.write(f"document_count: {meta.get('document_count', '<missing>')}")
        self.stdout.write(
            f"source_text_length: {meta.get('source_text_length', '<missing>')}"
        )
        self.stdout.write(f"full_name: {suggestion.get('full_name', '')}")
        self.stdout.write(f"email: {suggestion.get('email', '')}")
        self.stdout.write(f"location: {suggestion.get('location', '')}")
        self.stdout.write(
            "skills: " + ", ".join(suggestion.get("skills", [])[:8])
        )
        self.stdout.write(
            "tech_stack: " + ", ".join(suggestion.get("tech_stack", [])[:8])
        )
        self.stdout.write(
            f"education_summary: {suggestion.get('education_summary', '')}"
        )
