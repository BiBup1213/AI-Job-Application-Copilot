from rest_framework import serializers

from .models import EmailMessage


class EmailMessageSerializer(serializers.ModelSerializer):
    application_summary = serializers.SerializerMethodField()

    class Meta:
        model = EmailMessage
        fields = [
            "id",
            "application",
            "application_summary",
            "sender",
            "subject",
            "body",
            "received_at",
            "classification",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "application_summary"]

    def get_application_summary(self, obj):
        if not obj.application:
            return None
        return {
            "id": obj.application_id,
            "company": obj.application.job.company,
            "title": obj.application.job.title,
            "status": obj.application.status,
        }
