from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class JobPosting(models.Model):
    company = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=120, blank=True)
    source_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    requirements = models.JSONField(default=list, blank=True)
    nice_to_have = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    employment_type = models.CharField(max_length=80, blank=True)
    remote_type = models.CharField(max_length=80, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return f"{self.company} - {self.title}"


class JobMatch(models.Model):
    class Category(models.TextChoices):
        A = "A", "A"
        B = "B", "B"
        C = "C", "C"
        X = "X", "X"

    job = models.OneToOneField(
        JobPosting, on_delete=models.CASCADE, related_name="match"
    )
    score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    category = models.CharField(max_length=1, choices=Category.choices)
    strengths = models.JSONField(default=list, blank=True)
    risks = models.JSONField(default=list, blank=True)
    recommendation = models.TextField(blank=True)
    application_angle = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-score", "-created_at"]

    def __str__(self):
        return f"{self.job} ({self.score}%)"
