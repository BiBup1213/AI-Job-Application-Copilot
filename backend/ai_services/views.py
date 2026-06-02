from rest_framework.decorators import api_view
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView

from .document_extraction import extract_candidate_document_text
from .models import CandidateDocument, CandidateProfile
from .serializers import CandidateDocumentSerializer, CandidateProfileSerializer
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


class CandidateDocumentViewSet(ModelViewSet):
    queryset = CandidateDocument.objects.select_related("profile").all()
    serializer_class = CandidateDocumentSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def perform_create(self, serializer):
        profile = CandidateProfile.objects.first() or CandidateProfile.objects.create()
        document = serializer.save(profile=profile)
        status, extracted_text = extract_candidate_document_text(document)
        document.extraction_status = status
        document.extracted_text = extracted_text
        document.save(update_fields=["extraction_status", "extracted_text", "updated_at"])
