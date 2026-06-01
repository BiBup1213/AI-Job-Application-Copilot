from rest_framework import serializers

from .models import Application, ApplicationDocument, StatusEvent


class ApplicationJobSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    company = serializers.CharField()
    title = serializers.CharField()
    location = serializers.CharField()
    remote_type = serializers.CharField()


class ApplicationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationDocument
        fields = [
            "id",
            "application",
            "document_type",
            "title",
            "content",
            "version",
            "is_approved",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "application", "version", "created_at", "updated_at"]


class StatusEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusEvent
        fields = ["id", "application", "old_status", "new_status", "note", "created_at"]
        read_only_fields = ["id", "application", "created_at"]


class ApplicationSerializer(serializers.ModelSerializer):
    job_detail = ApplicationJobSerializer(source="job", read_only=True)
    documents = ApplicationDocumentSerializer(many=True, read_only=True)
    status_events = StatusEventSerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            "job",
            "job_detail",
            "status",
            "notes",
            "applied_at",
            "follow_up_at",
            "created_at",
            "updated_at",
            "documents",
            "status_events",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "documents", "status_events"]
