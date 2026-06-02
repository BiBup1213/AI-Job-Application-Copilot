from django.contrib import admin

from .models import CandidateDocument, CandidateProfile, CandidateProfileSuggestion


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
        "extracted_text_length",
        "use_for_ai_context",
        "updated_at",
    )
    list_filter = ("document_type", "extraction_status", "use_for_ai_context")
    search_fields = ("title", "original_filename", "extracted_text")
    readonly_fields = (
        "original_filename",
        "content_type",
        "file_size",
        "extracted_text_length",
        "extraction_error",
        "created_at",
        "updated_at",
    )


@admin.register(CandidateProfileSuggestion)
class CandidateProfileSuggestionAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "status", "created_at", "applied_at")
    list_filter = ("status",)
    readonly_fields = ("created_at", "updated_at", "applied_at")
    filter_horizontal = ("source_documents",)
