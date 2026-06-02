from django.db import models


class CandidateProfile(models.Model):
    full_name = models.CharField(max_length=160, blank=True)
    email = models.EmailField(blank=True)
    location = models.CharField(max_length=160, blank=True)
    target_roles = models.JSONField(default=list, blank=True)
    preferred_locations = models.JSONField(default=list, blank=True)
    remote_preference = models.CharField(max_length=120, blank=True)
    salary_expectation = models.CharField(max_length=120, blank=True)
    availability = models.CharField(max_length=160, blank=True)
    skills = models.JSONField(default=list, blank=True)
    tech_stack = models.JSONField(default=list, blank=True)
    projects = models.JSONField(default=list, blank=True)
    experience_summary = models.TextField(blank=True)
    education_summary = models.TextField(blank=True)
    strengths = models.JSONField(default=list, blank=True)
    no_gos = models.JSONField(default=list, blank=True)
    application_tone = models.CharField(max_length=160, blank=True)
    extra_context = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.full_name or "Kandidatenprofil"


class CandidateDocument(models.Model):
    class DocumentType(models.TextChoices):
        CV = "cv", "CV"
        CERTIFICATE = "certificate", "Certificate"
        REFERENCE = "reference", "Reference"
        COVER_LETTER_TEMPLATE = "cover_letter_template", "Cover letter template"
        OTHER = "other", "Other"

    class ExtractionStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        UNSUPPORTED = "unsupported", "Unsupported"

    profile = models.ForeignKey(
        CandidateProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    document_type = models.CharField(
        max_length=40,
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
    )
    title = models.CharField(max_length=220)
    file = models.FileField(upload_to="candidate_documents/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    extracted_text = models.TextField(blank=True)
    extracted_text_length = models.PositiveIntegerField(default=0)
    extraction_error = models.CharField(max_length=255, blank=True)
    extraction_status = models.CharField(
        max_length=20,
        choices=ExtractionStatus.choices,
        default=ExtractionStatus.PENDING,
    )
    use_for_ai_context = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.title


class CandidateProfileSuggestion(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPLIED = "applied", "Applied"
        DISMISSED = "dismissed", "Dismissed"

    profile = models.ForeignKey(
        CandidateProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suggestions",
    )
    source_documents = models.ManyToManyField(
        CandidateDocument,
        blank=True,
        related_name="profile_suggestions",
    )
    suggested_data = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Profilvorschlag #{self.pk}"
