from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CandidateProfile
from .serializers import CandidateProfileSerializer
from .services import dashboard_summary


@api_view(["GET"])
def dashboard_summary_view(request):
    return Response(dashboard_summary())


class CandidateProfileView(APIView):
    def get(self, request):
        profile = CandidateProfile.objects.first()
        if profile is None:
            return Response(CandidateProfileSerializer(CandidateProfile()).data)
        return Response(CandidateProfileSerializer(profile).data)

    def patch(self, request):
        profile = CandidateProfile.objects.first()
        if profile is None:
            serializer = CandidateProfileSerializer(data=request.data)
        else:
            serializer = CandidateProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
