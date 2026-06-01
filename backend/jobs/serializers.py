from rest_framework import serializers

from .models import JobMatch, JobPosting


class JobMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobMatch
        fields = [
            "id",
            "job",
            "score",
            "category",
            "strengths",
            "risks",
            "recommendation",
            "application_angle",
            "created_at",
        ]
        read_only_fields = ["id", "job", "created_at"]


class JobPostingSerializer(serializers.ModelSerializer):
    match = JobMatchSerializer(read_only=True)

    class Meta:
        model = JobPosting
        fields = [
            "id",
            "company",
            "title",
            "location",
            "source",
            "source_url",
            "description",
            "requirements",
            "nice_to_have",
            "tags",
            "employment_type",
            "remote_type",
            "published_at",
            "created_at",
            "updated_at",
            "match",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "match"]


class ManualJobPostingSerializer(serializers.ModelSerializer):
    source_url = serializers.URLField(required=False, allow_blank=True)
    requirements = serializers.ListField(
        child=serializers.CharField(allow_blank=False), required=False, allow_empty=True
    )
    nice_to_have = serializers.ListField(
        child=serializers.CharField(allow_blank=False), required=False, allow_empty=True
    )
    tags = serializers.ListField(
        child=serializers.CharField(allow_blank=False), required=False, allow_empty=True
    )

    class Meta:
        model = JobPosting
        fields = [
            "company",
            "title",
            "location",
            "source",
            "source_url",
            "description",
            "requirements",
            "nice_to_have",
            "tags",
            "employment_type",
            "remote_type",
        ]
        extra_kwargs = {
            "company": {"required": True, "allow_blank": False},
            "title": {"required": True, "allow_blank": False},
            "description": {"required": True, "allow_blank": False},
            "location": {"required": False, "allow_blank": True},
            "source": {"required": False, "allow_blank": True},
            "employment_type": {"required": False, "allow_blank": True},
            "remote_type": {"required": False, "allow_blank": True},
        }
