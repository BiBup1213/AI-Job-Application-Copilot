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

    def _next_document_version(self, application, document_type):
        latest = (
            application.documents.filter(document_type=document_type)
            .order_by("-version")
            .first()
        )
        return 1 if latest is None else latest.version + 1
