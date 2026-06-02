from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from ai_services.models import CandidateProfile
from ai_services.services import APPLICATION_ANGLE, classify_email_message
from applications.models import Application, ApplicationDocument, StatusEvent
from campaigns.models import SearchCampaign
from jobs.models import JobMatch, JobPosting
from mailcenter.models import EmailMessage


class Command(BaseCommand):
    help = "Seed demo data for the AI Job Application Copilot MVP."

    def handle(self, *args, **options):
        now = timezone.now()

        CandidateProfile.objects.update_or_create(
            id=1,
            defaults={
                "full_name": "Max Beispiel",
                "email": "max.beispiel@gmail.com",
                "location": "Braunschweig",
                "target_roles": [
                    "Junior Softwareentwickler",
                    "Python Developer",
                    "Web Developer",
                    "Automation Specialist",
                ],
                "preferred_locations": ["Braunschweig", "Hannover", "Remote"],
                "remote_preference": "Remote oder Hybrid bevorzugt",
                "salary_expectation": "",
                "availability": "Kurzfristig nach Absprache",
                "skills": [
                    "Python",
                    "Django",
                    "JavaScript",
                    "REST APIs",
                    "SQL",
                    "Automatisierung",
                    "E-Commerce-Prozesse",
                ],
                "tech_stack": ["Python", "Django", "React Grundlagen", "Docker", "Git"],
                "projects": [
                    "Webentwicklung und API-Integrationen",
                    "Automatisierung wiederkehrender Abläufe",
                    "E-Commerce-Prozessverbesserungen",
                ],
                "experience_summary": (
                    "Praktisch geprägter Entwickler mit Fokus auf Webentwicklung, "
                    "Automatisierung und schneller Einarbeitung in produktnahe Abläufe."
                ),
                "education_summary": "",
                "strengths": [
                    "pragmatische Umsetzung",
                    "schnelle Einarbeitung",
                    "klarer Blick für Prozesse",
                ],
                "no_gos": ["reine Senior-Rollen", "starker Sales-Fokus"],
                "application_tone": "professionell, konkret und nicht übertrieben",
                "extra_context": "Bewerbungen sollen auf Deutsch und mit Human-in-the-loop Prüfung entstehen.",
            },
        )

        campaigns = [
            {
                "name": "Python Webentwicklung Braunschweig",
                "keywords": ["Python", "Django", "Webentwicklung", "Junior"],
                "industries": ["Software", "E-Commerce", "IT-Dienstleistung"],
                "sources": ["StepStone", "LinkedIn", "Indeed"],
                "location": "Braunschweig",
                "radius_km": 35,
                "remote_allowed": True,
                "hybrid_allowed": True,
                "exclude_keywords": ["Senior", "Lead", "SAP"],
                "status": SearchCampaign.Status.ACTIVE,
            },
            {
                "name": "Automation und AI Operations",
                "keywords": ["Automation", "AI", "Prozessautomatisierung", "Python"],
                "industries": ["Handel", "E-Commerce", "IT"],
                "sources": ["LinkedIn", "Unternehmensseiten"],
                "location": "Remote",
                "radius_km": 100,
                "remote_allowed": True,
                "hybrid_allowed": False,
                "exclude_keywords": ["Data Scientist Senior", "PhD"],
                "status": SearchCampaign.Status.DRAFT,
            },
        ]
        for payload in campaigns:
            SearchCampaign.objects.update_or_create(
                name=payload["name"],
                defaults=payload,
            )

        jobs = [
            {
                "company": "TRIOLOGY GmbH",
                "title": "Junior Softwareentwickler Python / Web",
                "location": "Braunschweig",
                "source": "Demo StepStone",
                "source_url": "https://example.test/demo/triology-junior-python-web",
                "description": "Juniorrolle mit Python, Webentwicklung, APIs und agiler Zusammenarbeit.",
                "requirements": ["Python", "Webentwicklung", "Git", "REST APIs"],
                "nice_to_have": ["Django", "Docker", "Automatisierung"],
                "tags": ["python", "web", "django", "junior"],
                "employment_type": "Vollzeit",
                "remote_type": "hybrid",
                "published_at": now - timedelta(days=1),
                "score": 91,
            },
            {
                "company": "KOSATEC Computer GmbH",
                "title": "AI Enthusiast / Automation Specialist",
                "location": "Braunschweig",
                "source": "Demo LinkedIn",
                "source_url": "https://example.test/demo/kosatec-ai-automation",
                "description": "Automatisierung von internen Workflows und Entwicklung kleiner AI-Prototypen.",
                "requirements": ["Automatisierung", "Python", "Prozessanalyse"],
                "nice_to_have": ["E-Commerce", "APIs", "KI-Tools"],
                "tags": ["ai", "automation", "python", "operations"],
                "employment_type": "Vollzeit",
                "remote_type": "hybrid",
                "published_at": now - timedelta(days=2),
                "score": 88,
            },
            {
                "company": "Beispiel Commerce AG",
                "title": "E-Commerce Developer / Web Operations",
                "location": "Remote",
                "source": "Demo Indeed",
                "source_url": "https://example.test/demo/beispiel-commerce-web-ops",
                "description": "Shop-nahe Webentwicklung, Schnittstellenpflege und Prozessautomatisierung.",
                "requirements": ["E-Commerce", "Webentwicklung", "SQL"],
                "nice_to_have": ["Python", "Monitoring", "APIs"],
                "tags": ["e-commerce", "web", "automation"],
                "employment_type": "Vollzeit",
                "remote_type": "remote",
                "published_at": now - timedelta(days=3),
                "score": 83,
            },
            {
                "company": "Stadt Wolfenbüttel",
                "title": "IT-Servicedesk Mitarbeiter*in",
                "location": "Wolfenbüttel",
                "source": "Demo Kommunalportal",
                "source_url": "https://example.test/demo/stadt-wf-servicedesk",
                "description": "IT-Support, Ticketbearbeitung und Betreuung kommunaler Fachverfahren.",
                "requirements": ["IT-Support", "Windows", "Ticket-Systeme"],
                "nice_to_have": ["Automatisierung", "Dokumentation", "Serviceorientierung"],
                "tags": ["servicedesk", "support", "it"],
                "employment_type": "Vollzeit",
                "remote_type": "onsite",
                "published_at": now - timedelta(days=4),
                "score": 76,
            },
        ]

        created_jobs = []
        for payload in jobs:
            payload = payload.copy()
            score = payload.pop("score")
            job, _ = JobPosting.objects.update_or_create(
                source_url=payload["source_url"],
                defaults=payload,
            )
            JobMatch.objects.update_or_create(
                job=job,
                defaults={
                    "score": score,
                    "category": "A" if score >= 85 else "B",
                    "strengths": [
                        "Passende Überschneidung mit praktischer Umsetzung.",
                        "Guter Anknüpfungspunkt für Webentwicklung und Automatisierung.",
                    ],
                    "risks": [
                        "Anforderungen vor Versand noch manuell mit Lebenslauf abgleichen."
                    ],
                    "recommendation": "Gute Demo-Priorität für das MVP.",
                    "application_angle": APPLICATION_ANGLE,
                },
            )
            created_jobs.append(job)

        statuses = [
            Application.Status.DRAFT_OPEN,
            Application.Status.DRAFT_APPROVED,
            Application.Status.APPLIED,
            Application.Status.FOLLOW_UP_DUE,
        ]
        applications = []
        for index, job in enumerate(created_jobs):
            application = Application.objects.filter(job=job).first()
            defaults = {
                "status": statuses[index],
                "notes": "Demo-Bewerbung für Human-in-the-loop Workflow.",
                "follow_up_at": now - timedelta(days=1) if index == 3 else now + timedelta(days=5),
            }
            if statuses[index] == Application.Status.APPLIED:
                defaults["applied_at"] = now - timedelta(days=2)
            if application:
                for field, value in defaults.items():
                    setattr(application, field, value)
                application.save()
            else:
                application = Application.objects.create(job=job, **defaults)
            applications.append(application)
            StatusEvent.objects.get_or_create(
                application=application,
                old_status="",
                new_status=Application.Status.NEW,
                note="Demo-Bewerbung angelegt.",
            )
            if application.status != Application.Status.NEW:
                StatusEvent.objects.get_or_create(
                    application=application,
                    old_status=Application.Status.NEW,
                    new_status=application.status,
                    note="Demo-Status gesetzt.",
                )

        for application in applications[:2]:
            ApplicationDocument.objects.get_or_create(
                application=application,
                document_type=ApplicationDocument.DocumentType.EMAIL,
                version=1,
                defaults={
                    "title": f"Bewerbung als {application.job.title}",
                    "content": (
                        "Sehr geehrtes Recruiting-Team,\n\n"
                        "anbei erhalten Sie meine Bewerbung. Der Entwurf ist bewusst "
                        "als prüfbarer MVP-Text angelegt.\n\n"
                        "Mit freundlichen Grüßen\nMax Beispiel"
                    ),
                    "is_approved": application.status == Application.Status.DRAFT_APPROVED,
                },
            )

        email_payloads = [
            {
                "application": applications[0],
                "sender": "recruiting@triology.example",
                "subject": "Bestätigung Ihrer Bewerbung",
                "body": "Vielen Dank, Ihre Bewerbung ist bei uns eingegangen.",
                "received_at": now - timedelta(hours=8),
            },
            {
                "application": applications[1],
                "sender": "jobs@kosatec.example",
                "subject": "Rückfrage zu Ihrem Profil",
                "body": "Wir haben eine Rückfrage zu Ihren Automatisierungsprojekten.",
                "received_at": now - timedelta(days=1),
            },
            {
                "application": applications[2],
                "sender": "karriere@commerce.example",
                "subject": "Einladung zum Kennenlernen",
                "body": "Wir möchten Sie gerne zu einem ersten Gespräch einladen.",
                "received_at": now - timedelta(days=2),
            },
        ]
        for payload in email_payloads:
            email, _ = EmailMessage.objects.update_or_create(
                sender=payload["sender"],
                subject=payload["subject"],
                defaults=payload,
            )
            classify_email_message(email)

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
