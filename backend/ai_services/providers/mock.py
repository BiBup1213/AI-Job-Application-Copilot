from ai_services.profile_payload import candidate_display_name, get_candidate_profile_payload
from applications.models import ApplicationDocument
from jobs.models import JobMatch
from mailcenter.models import EmailMessage


APPLICATION_ANGLE = (
    "Nicht als reiner Junior verkaufen, sondern als praktisch geprägter Entwickler "
    "mit Erfahrung in Webentwicklung, Automatisierung, E-Commerce-Prozessen und "
    "schneller Einarbeitung."
)


class MockAIProvider:
    def evaluate_job_match(self, job):
        score = self._score_for_job(job)
        strengths = [
            "Gute Überschneidung mit praktischer Webentwicklung.",
            "Automatisierungs- und Prozessdenken lassen sich klar positionieren.",
        ]
        risks = []
        if score < 80:
            risks.append(
                "Einige Anforderungen sollten vor einer Bewerbung manuell geprüft werden."
            )
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
                "category": self._category_for_score(score),
                "strengths": strengths,
                "risks": risks,
                "recommendation": recommendation,
                "application_angle": APPLICATION_ANGLE,
            },
        )
        return job_match

    def generate_application_documents(self, application):
        job = application.job
        match = getattr(job, "match", None) or self.evaluate_job_match(job)
        display_name = candidate_display_name()
        next_cover_version = self._next_document_version(
            application, ApplicationDocument.DocumentType.COVER_LETTER
        )
        next_email_version = self._next_document_version(
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
                f"{display_name}"
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
                f"{display_name}"
            ),
        )
        return [cover_letter, email]

    def generate_follow_up_document(self, application):
        job = application.job
        display_name = candidate_display_name()
        next_version = self._next_document_version(
            application, ApplicationDocument.DocumentType.FOLLOW_UP
        )
        document = ApplicationDocument.objects.create(
            application=application,
            document_type=ApplicationDocument.DocumentType.FOLLOW_UP,
            title=f"Follow-up zur Bewerbung als {job.title}",
            version=next_version,
            content=(
                "Sehr geehrtes Recruiting-Team,\n\n"
                f"ich wollte mich kurz nach dem aktuellen Stand meiner Bewerbung für die "
                f"Position {job.title} erkundigen. Die Aufgabe bei {job.company} "
                "interessiert mich weiterhin sehr.\n\n"
                "Falls es bereits einen Zwischenstand gibt oder noch Unterlagen fehlen, "
                "freue ich mich über eine kurze Rückmeldung.\n\n"
                "Vielen Dank und freundliche Grüße\n"
                f"{display_name}"
            ),
        )
        return document

    def classify_email_message(self, email):
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

    def suggest_profile_from_documents(self, profile, documents):
        text = self._document_text(documents)
        lower_text = text.lower()
        titles = [document.title for document in documents]
        skills = self._matched_terms(
            lower_text,
            [
                "Python",
                "Django",
                "JavaScript",
                "React",
                "REST APIs",
                "SQL",
                "Docker",
                "Git",
                "Automatisierung",
                "E-Commerce",
                "Shopify",
                "API",
            ],
        )
        tech_stack = self._matched_terms(
            lower_text,
            ["Python", "Django", "React", "JavaScript", "Docker", "Git", "SQL"]
        )
        target_roles = []
        if any(word in lower_text for word in ["python", "django", "software"]):
            target_roles.append("Junior Softwareentwickler")
        if any(word in lower_text for word in ["web", "frontend", "react"]):
            target_roles.append("Web Developer")
        if any(word in lower_text for word in ["automation", "automatisierung"]):
            target_roles.append("Automation Specialist")
        if not target_roles and any(
            word in lower_text for word in ["lebenslauf", "cv", "resume"]
        ):
            target_roles.extend(["Junior Softwareentwickler", "Web Developer"])
        projects = []
        if any(word in lower_text for word in ["e-commerce", "shop", "commerce"]):
            projects.append("E-Commerce-Prozesse und Shop-nahe Webentwicklung")
        if any(word in lower_text for word in ["api", "schnittstelle", "rest"]):
            projects.append("API- und Schnittstellenarbeit")
        if any(word in lower_text for word in ["automation", "automatisierung"]):
            projects.append("Automatisierung wiederkehrender Abläufe")

        confidence_notes = []
        missing_information = []
        if text.strip():
            confidence_notes.append(
                "Mock-Auswertung basiert auf verfügbaren Dokumentinhalten und Metadaten."
            )
        else:
            missing_information.append(
                "Es wurden keine nutzbaren Dokumentinformationen gefunden."
            )
        weak_text_documents = [
            document.title
            for document in documents
            if not (document.extracted_text or "").strip()
        ]
        if weak_text_documents:
            confidence_notes.append(
                "Einige Unterlagen liefern nur Metadaten oder keinen auslesbaren Text: "
                + ", ".join(weak_text_documents[:5])
            )
        if titles:
            confidence_notes.append(
                "Berücksichtigte Unterlagen: " + ", ".join(titles[:5])
            )

        return {
            "full_name": "",
            "email": "",
            "location": "",
            "target_roles": target_roles,
            "preferred_locations": [],
            "remote_preference": "",
            "salary_expectation": "",
            "availability": "",
            "skills": skills,
            "tech_stack": tech_stack,
            "projects": projects,
            "experience_summary": self._experience_summary(skills, projects),
            "education_summary": "",
            "strengths": [
                "praktische Umsetzung",
                "schnelle Einarbeitung",
                "strukturierter Umgang mit digitalen Prozessen",
            ]
            if skills or projects
            else [],
            "no_gos": [],
            "application_tone": "professionell, konkret und nicht übertrieben",
            "extra_context": (
                "Profilvorschlag aus hochgeladenen Bewerbungsunterlagen. "
                "Bitte manuell prüfen, bevor daraus neue Bewerbungen entstehen."
            )
            if documents
            else "",
            "confidence_notes": confidence_notes,
            "missing_information": missing_information,
            "_meta": self._suggestion_meta(documents, text),
        }

    def _category_for_score(self, score):
        if score >= 85:
            return JobMatch.Category.A
        if score >= 75:
            return JobMatch.Category.B
        if score >= 60:
            return JobMatch.Category.C
        return JobMatch.Category.X

    def _score_for_job(self, job):
        profile = get_candidate_profile_payload()
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
                " ".join(str(item) for item in profile.get("skills", [])),
                " ".join(str(item) for item in profile.get("tech_stack", [])),
                profile.get("experience_summary", ""),
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
        for no_go in profile.get("no_gos", []):
            if isinstance(no_go, str) and no_go.strip().lower() in text:
                score -= 8
        if job.remote_type in ["remote", "hybrid"]:
            score += 3
        return max(0, min(100, score))

    def _document_text(self, documents):
        return "\n\n".join(
            [
                "\n".join(
                    [
                        document.title,
                        document.document_type,
                        document.original_filename,
                        document.notes or "",
                        document.extraction_status,
                        document.extraction_error or "",
                        document.extracted_text or "",
                    ]
                )
                for document in documents
            ]
        )

    def _suggestion_meta(self, documents, text):
        fallback_reason = getattr(self, "fallback_reason", "")
        return {
            "provider_used": "mock",
            "fallback_used": bool(fallback_reason),
            "fallback_reason": fallback_reason or "AI_PROVIDER=mock",
            "source_text_length": len(text),
            "document_count": len(documents),
        }

    def _matched_terms(self, lower_text, terms):
        matches = []
        for term in terms:
            if term.lower() in lower_text and term not in matches:
                matches.append(term)
        return matches

    def _experience_summary(self, skills, projects):
        parts = []
        if skills:
            parts.append("Kenntnisse in " + ", ".join(skills[:6]))
        if projects:
            parts.append("praktische Berührungspunkte mit " + ", ".join(projects[:3]))
        if not parts:
            return ""
        return ". ".join(parts) + "."

    def _next_document_version(self, application, document_type):
        latest = (
            application.documents.filter(document_type=document_type)
            .order_by("-version")
            .first()
        )
        return 1 if latest is None else latest.version + 1
