from rest_framework import serializers

from .document_extraction import MAX_UPLOAD_SIZE, is_supported_document
from .models import CandidateDocument, CandidateProfile


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


class CandidateDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = CandidateDocument
        fields = [
            "id",
            "profile",
            "document_type",
            "title",
            "file",
            "file_url",
            "original_filename",
            "content_type",
            "file_size",
            "extracted_text",
            "extraction_status",
            "use_for_ai_context",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "profile",
            "file_url",
            "original_filename",
            "content_type",
            "file_size",
            "extraction_status",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "file": {"write_only": True, "required": False},
            "title": {"required": False},
        }

    def validate(self, attrs):
        file = attrs.get("file")
        if self.instance is None and file is None:
            raise serializers.ValidationError({"file": "Eine Datei ist erforderlich."})
        if file is not None:
            if file.size > MAX_UPLOAD_SIZE:
                raise serializers.ValidationError(
                    {"file": "Die Datei darf maximal 10 MB groß sein."}
                )
            if not is_supported_document(file.name):
                raise serializers.ValidationError(
                    {"file": "Unterstützt werden nur PDF-, DOCX- und TXT-Dateien."}
                )
        return attrs

    def create(self, validated_data):
        file = validated_data["file"]
        title = validated_data.get("title") or file.name
        validated_data.update(
            {
                "title": title,
                "original_filename": file.name,
                "content_type": getattr(file, "content_type", "") or "",
                "file_size": file.size,
            }
        )
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "extracted_text" in validated_data and validated_data["extracted_text"].strip():
            validated_data["extraction_status"] = CandidateDocument.ExtractionStatus.SUCCESS
        return super().update(instance, validated_data)

    def get_file_url(self, obj):
        if not obj.file:
            return ""
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url
