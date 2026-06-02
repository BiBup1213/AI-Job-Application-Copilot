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
