from django.contrib import admin

from .models import CandidateProfile


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "location", "updated_at")
    search_fields = ("full_name", "email", "location")
    readonly_fields = ("created_at", "updated_at")
