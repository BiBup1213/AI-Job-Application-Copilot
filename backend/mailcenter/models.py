from django.db import models


class EmailMessage(models.Model):
    class Classification(models.TextChoices):
        CONFIRMATION = "confirmation", "Confirmation"
        REJECTION = "rejection", "Rejection"
        INVITATION = "invitation", "Invitation"
        QUESTION = "question", "Question"
        FOLLOW_UP = "follow_up", "Follow-up"
        UNKNOWN = "unknown", "Unknown"
        REQUIRES_ACTION = "requires_action", "Requires action"

    application = models.ForeignKey(
        "applications.Application",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emails",
    )
    sender = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    received_at = models.DateTimeField()
    classification = models.CharField(
        max_length=40,
        choices=Classification.choices,
        default=Classification.UNKNOWN,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at", "-created_at"]

    def __str__(self):
        return self.subject
