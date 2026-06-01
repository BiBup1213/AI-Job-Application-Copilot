from django.contrib import admin

from .models import JobMatch, JobPosting


class JobMatchInline(admin.StackedInline):
    model = JobMatch
    extra = 0
    can_delete = False


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ("company", "title", "location", "source", "remote_type", "created_at")
    list_filter = ("source", "remote_type", "employment_type")
    search_fields = ("company", "title", "location", "description")
    inlines = [JobMatchInline]


@admin.register(JobMatch)
class JobMatchAdmin(admin.ModelAdmin):
    list_display = ("job", "score", "category", "created_at")
    list_filter = ("category",)
    search_fields = ("job__company", "job__title", "recommendation")
