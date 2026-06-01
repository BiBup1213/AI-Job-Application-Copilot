from rest_framework import serializers

from .models import EmailMessage


class EmailMessageSerializer(serializers.ModelSerializer):
    application_summary = serializers.SerializerMethodField()
    application_company = serializers.SerializerMethodField()
    application_job_title = serializers.SerializerMethodField()
    requires_action = serializers.SerializerMethodField()

    class Meta:
        model = EmailMessage
        fields = [
            "id",
            "application",
            "application_summary",
            "application_company",
            "application_job_title",
            "sender",
            "subject",
            "body",
            "received_at",
            "classification",
            "requires_action",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "application_summary",
            "application_company",
            "application_job_title",
            "sender",
            "subject",
            "body",
            "received_at",
            "classification",
            "requires_action",
            "created_at",
        ]

    def get_application_summary(self, obj):
        if not obj.application:
            return None
        return {
            "id": obj.application_id,
            "company": obj.application.job.company,
            "title": obj.application.job.title,
            "status": obj.application.status,
        }

    def get_application_company(self, obj):
        if not obj.application:
            return ""
        return obj.application.job.company

    def get_application_job_title(self, obj):
        if not obj.application:
            return ""
        return obj.application.job.title

    def get_requires_action(self, obj):
        return obj.classification in [
            EmailMessage.Classification.INVITATION,
            EmailMessage.Classification.QUESTION,
            EmailMessage.Classification.FOLLOW_UP,
            EmailMessage.Classification.REQUIRES_ACTION,
        ]
