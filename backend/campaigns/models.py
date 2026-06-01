from django.db import models


class SearchCampaign(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        COMPLETED = "completed", "Completed"

    name = models.CharField(max_length=255)
    keywords = models.JSONField(default=list, blank=True)
    industries = models.JSONField(default=list, blank=True)
    sources = models.JSONField(default=list, blank=True)
    location = models.CharField(max_length=255, blank=True)
    radius_km = models.PositiveIntegerField(default=25)
    remote_allowed = models.BooleanField(default=True)
    hybrid_allowed = models.BooleanField(default=True)
    exclude_keywords = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
