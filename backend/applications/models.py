from django.db import models


class Application(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        INTERESTING = "interesting", "Interesting"
        DRAFT_OPEN = "draft_open", "Draft open"
        DRAFT_APPROVED = "draft_approved", "Draft approved"
        GMAIL_DRAFT_CREATED = "gmail_draft_created", "Gmail draft created"
        APPLIED = "applied", "Applied"
        RESPONSE_RECEIVED = "response_received", "Response received"
        INTERVIEW = "interview", "Interview"
        REJECTED = "rejected", "Rejected"
        FOLLOW_UP_DUE = "follow_up_due", "Follow-up due"
        CLOSED = "closed", "Closed"

    job = models.ForeignKey(
        "jobs.JobPosting", on_delete=models.CASCADE, related_name="applications"
    )
    status = models.CharField(max_length=40, choices=Status.choices, default=Status.NEW)
    notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    follow_up_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def __str__(self):
        return f"{self.job.company} - {self.job.title} ({self.status})"


class ApplicationDocument(models.Model):
    class DocumentType(models.TextChoices):
        COVER_LETTER = "cover_letter", "Cover letter"
        EMAIL = "email", "Email"
        FOLLOW_UP = "follow_up", "Follow-up"
        REPLY = "reply", "Reply"

    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(max_length=40, choices=DocumentType.choices)
    title = models.CharField(max_length=255)
    content = models.TextField()
    version = models.PositiveIntegerField(default=1)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["application", "document_type", "-version"]
        unique_together = ("application", "document_type", "version")

    def __str__(self):
        return f"{self.title} v{self.version}"


class StatusEvent(models.Model):
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="status_events"
    )
    old_status = models.CharField(max_length=40, blank=True)
    new_status = models.CharField(max_length=40)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.old_status} -> {self.new_status}"
