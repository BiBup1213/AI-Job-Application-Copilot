from rest_framework import serializers

from .models import SearchCampaign


class SearchCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchCampaign
        fields = [
            "id",
            "name",
            "keywords",
            "industries",
            "sources",
            "location",
            "radius_km",
            "remote_allowed",
            "hybrid_allowed",
            "exclude_keywords",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
