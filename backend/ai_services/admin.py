from django.contrib import admin

from .models import CandidateDocument, CandidateProfile


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "location", "updated_at")
    search_fields = ("full_name", "email", "location")
    readonly_fields = ("created_at", "updated_at")


@admin.register(CandidateDocument)
class CandidateDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "document_type",
        "original_filename",
        "extraction_status",
        "use_for_ai_context",
        "updated_at",
    )
    list_filter = ("document_type", "extraction_status", "use_for_ai_context")
    search_fields = ("title", "original_filename", "extracted_text")
    readonly_fields = (
        "original_filename",
        "content_type",
        "file_size",
        "created_at",
        "updated_at",
    )
