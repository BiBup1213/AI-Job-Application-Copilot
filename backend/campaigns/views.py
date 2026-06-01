from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ai_services.services import create_mock_jobs_for_campaign

from .models import SearchCampaign
from .serializers import SearchCampaignSerializer


class SearchCampaignViewSet(viewsets.ModelViewSet):
    queryset = SearchCampaign.objects.all()
    serializer_class = SearchCampaignSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    @action(detail=True, methods=["post"], url_path="run")
    def run(self, request, pk=None):
        campaign = self.get_object()
        jobs = create_mock_jobs_for_campaign(campaign)
        campaign.status = SearchCampaign.Status.ACTIVE
        campaign.save(update_fields=["status", "updated_at"])
        return Response(
            {
                "message": "Mock-Kampagnenlauf abgeschlossen.",
                "created_jobs": len(jobs),
                "job_ids": [job.id for job in jobs],
            },
            status=status.HTTP_201_CREATED,
        )
