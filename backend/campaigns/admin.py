from django.contrib import admin

from .models import SearchCampaign


@admin.register(SearchCampaign)
class SearchCampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "status", "remote_allowed", "updated_at")
    list_filter = ("status", "remote_allowed", "hybrid_allowed")
    search_fields = ("name", "location")
