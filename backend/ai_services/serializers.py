from rest_framework import serializers

from .models import CandidateProfile


class CandidateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateProfile
        fields = [
            "id",
            "full_name",
            "email",
            "location",
            "target_roles",
            "preferred_locations",
            "remote_preference",
            "salary_expectation",
            "availability",
            "skills",
            "tech_stack",
            "projects",
            "experience_summary",
            "education_summary",
            "strengths",
            "no_gos",
            "application_tone",
            "extra_context",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        for field_name in [
            "target_roles",
            "preferred_locations",
            "skills",
            "tech_stack",
            "projects",
            "strengths",
            "no_gos",
        ]:
            if field_name in attrs and not isinstance(attrs[field_name], list):
                raise serializers.ValidationError(
                    {field_name: "Dieses Feld muss eine Liste sein."}
                )
        return attrs
