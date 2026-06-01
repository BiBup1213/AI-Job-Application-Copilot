from django.contrib import admin

from .models import Application, ApplicationDocument, StatusEvent


class ApplicationDocumentInline(admin.TabularInline):
    model = ApplicationDocument
    extra = 0


class StatusEventInline(admin.TabularInline):
    model = StatusEvent
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "status", "applied_at", "follow_up_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("job__company", "job__title", "notes")
    inlines = [ApplicationDocumentInline, StatusEventInline]


@admin.register(ApplicationDocument)
class ApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "application", "document_type", "version", "is_approved")
    list_filter = ("document_type", "is_approved")
    search_fields = ("title", "content", "application__job__company")


@admin.register(StatusEvent)
class StatusEventAdmin(admin.ModelAdmin):
    list_display = ("application", "old_status", "new_status", "created_at")
    list_filter = ("new_status",)
    search_fields = ("application__job__company", "note")
