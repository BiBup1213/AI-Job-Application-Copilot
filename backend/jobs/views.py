from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ai_services.services import evaluate_job_match
from applications.models import Application, StatusEvent
from applications.serializers import ApplicationSerializer

from .models import JobPosting
from .serializers import (
    JobMatchSerializer,
    JobPostingSerializer,
    ManualJobPostingSerializer,
)


class JobPostingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = JobPosting.objects.select_related("match").all()
    serializer_class = JobPostingSerializer

    @action(detail=True, methods=["post"], url_path="evaluate")
    def evaluate(self, request, pk=None):
        job = self.get_object()
        job_match = evaluate_job_match(job)
        return Response(JobMatchSerializer(job_match).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="manual-import")
    def manual_import(self, request):
        serializer = ManualJobPostingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save()
        evaluate_job_match(job)
        job = JobPosting.objects.select_related("match").get(pk=job.pk)
        return Response(JobPostingSerializer(job).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="create-application")
    def create_application(self, request, pk=None):
        job = self.get_object()
        application, created = Application.objects.get_or_create(
            job=job,
            defaults={
                "status": Application.Status.NEW,
                "notes": "Aus Stellenanzeige erstellt. Bitte manuell prüfen.",
            },
        )
        if created:
            StatusEvent.objects.create(
                application=application,
                old_status="",
                new_status=Application.Status.NEW,
                note="Bewerbung aus Jobposting angelegt.",
            )
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(ApplicationSerializer(application).data, status=response_status)
