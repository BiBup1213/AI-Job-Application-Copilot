from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ai_services.services import generate_application_documents

from .models import Application, ApplicationDocument, StatusEvent
from .serializers import ApplicationDocumentSerializer, ApplicationSerializer


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = (
        Application.objects.select_related("job")
        .select_related("job__match")
        .prefetch_related("documents", "status_events")
        .all()
    )
    serializer_class = ApplicationSerializer
    http_method_names = ["get", "patch", "post", "head", "options"]

    def perform_update(self, serializer):
        old_status = self.get_object().status
        application = serializer.save()
        if old_status != application.status:
            StatusEvent.objects.create(
                application=application,
                old_status=old_status,
                new_status=application.status,
                note="Status manuell aktualisiert.",
            )

    @action(detail=True, methods=["post"], url_path="generate-documents")
    def generate_documents(self, request, pk=None):
        application = self.get_object()
        documents = generate_application_documents(application)
        if application.status in [Application.Status.NEW, Application.Status.INTERESTING]:
            old_status = application.status
            application.status = Application.Status.DRAFT_OPEN
            application.save(update_fields=["status", "updated_at"])
            StatusEvent.objects.create(
                application=application,
                old_status=old_status,
                new_status=application.status,
                note="Dokumententwurfe wurden generiert.",
            )
        return Response(
            ApplicationDocumentSerializer(documents, many=True).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="approve-document")
    def approve_document(self, request, pk=None):
        application = self.get_object()
        document_id = request.data.get("document_id")
        queryset = application.documents.all()
        if document_id:
            queryset = queryset.filter(id=document_id)
        document = queryset.order_by("-created_at").first()
        if not document:
            return Response(
                {"detail": "Kein Dokument zum Freigeben gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )
        document.is_approved = True
        document.save(update_fields=["is_approved", "updated_at"])
        if application.documents.filter(is_approved=True).exists():
            old_status = application.status
            application.status = Application.Status.DRAFT_APPROVED
            application.save(update_fields=["status", "updated_at"])
            if old_status != application.status:
                StatusEvent.objects.create(
                    application=application,
                    old_status=old_status,
                    new_status=application.status,
                    note=f"Dokument freigegeben: {document.title}",
                )
        return Response(ApplicationDocumentSerializer(document).data)

    @action(
        detail=True,
        methods=["patch"],
        url_path=r"documents/(?P<document_id>[^/.]+)",
    )
    def update_document(self, request, pk=None, document_id=None):
        application = self.get_object()
        document = application.documents.filter(id=document_id).first()
        if not document:
            return Response(
                {"detail": "Dokument nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )

        old_title = document.title
        old_content = document.content
        title = request.data.get("title")
        content = request.data.get("content")

        if title is not None:
            document.title = title
        if content is not None:
            document.content = content

        changed = document.title != old_title or document.content != old_content
        update_fields = ["updated_at"]
        if title is not None:
            update_fields.append("title")
        if content is not None:
            update_fields.append("content")

        if changed and document.is_approved:
            document.is_approved = False
            update_fields.append("is_approved")
            old_status = application.status
            if application.status in [
                Application.Status.DRAFT_APPROVED,
                Application.Status.GMAIL_DRAFT_CREATED,
            ]:
                application.status = Application.Status.DRAFT_OPEN
                application.save(update_fields=["status", "updated_at"])
            StatusEvent.objects.create(
                application=application,
                old_status=old_status,
                new_status=application.status,
                note=f"Freigabe zurückgesetzt nach Bearbeitung: {document.title}",
            )
        elif changed:
            StatusEvent.objects.create(
                application=application,
                old_status=application.status,
                new_status=application.status,
                note=f"Dokument bearbeitet: {document.title}",
            )

        document.save(update_fields=update_fields)
        return Response(ApplicationDocumentSerializer(document).data)

    @action(detail=True, methods=["post"], url_path="create-gmail-draft")
    def create_gmail_draft(self, request, pk=None):
        application = self.get_object()
        approved_email = application.documents.filter(
            document_type=ApplicationDocument.DocumentType.EMAIL,
            is_approved=True,
        ).first()
        if not approved_email:
            return Response(
                {"detail": "Bitte zuerst einen E-Mail-Entwurf freigeben."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        old_status = application.status
        application.status = Application.Status.GMAIL_DRAFT_CREATED
        application.save(update_fields=["status", "updated_at"])
        if old_status != application.status:
            StatusEvent.objects.create(
                application=application,
                old_status=old_status,
                new_status=application.status,
                note="Gmail-Entwurf simuliert erstellt. Es wurde nichts versendet.",
            )
        return Response(
            {
                "message": "Gmail-Entwurf wurde simuliert. Kein Versand, keine Gmail API.",
                "draft_subject": approved_email.title,
            }
        )

    @action(detail=True, methods=["post"], url_path="mark-applied")
    def mark_applied(self, request, pk=None):
        application = self.get_object()
        old_status = application.status
        application.status = Application.Status.APPLIED
        application.applied_at = timezone.now()
        application.save(update_fields=["status", "applied_at", "updated_at"])
        StatusEvent.objects.create(
            application=application,
            old_status=old_status,
            new_status=application.status,
            note="Bewerbung als versendet markiert.",
        )
        return Response(ApplicationSerializer(application).data)
