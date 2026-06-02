from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView

from .document_extraction import apply_extraction_result, extract_candidate_document_text
from .models import CandidateDocument, CandidateProfile, CandidateProfileSuggestion
from .serializers import (
    CandidateDocumentSerializer,
    CandidateProfileSerializer,
    CandidateProfileSuggestionSerializer,
)
from .services import (
    apply_profile_suggestion,
    dashboard_summary,
    suggest_profile_from_documents,
)


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
        apply_extraction_result(document, extract_candidate_document_text(document))

    @action(detail=True, methods=["post"], url_path="reextract")
    def reextract(self, request, pk=None):
        document = self.get_object()
        apply_extraction_result(document, extract_candidate_document_text(document))
        return Response(self.get_serializer(document).data)


class CandidateProfileSuggestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CandidateProfileSuggestion.objects.select_related("profile").prefetch_related(
        "source_documents"
    )
    serializer_class = CandidateProfileSuggestionSerializer
    http_method_names = ["get", "post", "head", "options"]

    @action(detail=True, methods=["post"], url_path="apply")
    def apply(self, request, pk=None):
        suggestion = self.get_object()
        apply_profile_suggestion(suggestion)
        return Response(self.get_serializer(suggestion).data)

    @action(detail=True, methods=["post"], url_path="dismiss")
    def dismiss(self, request, pk=None):
        suggestion = self.get_object()
        suggestion.status = CandidateProfileSuggestion.Status.DISMISSED
        suggestion.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(suggestion).data)


class CandidateProfileSuggestFromDocumentsView(APIView):
    def post(self, request):
        profile = CandidateProfile.objects.first() or CandidateProfile.objects.create()
        document_ids = request.data.get("document_ids") or []
        documents = self._documents_for_request(profile, document_ids)
        suggested_data = suggest_profile_from_documents(profile, list(documents))
        suggestion = CandidateProfileSuggestion.objects.create(
            profile=profile,
            suggested_data=suggested_data,
        )
        suggestion.source_documents.set(documents)
        serializer = CandidateProfileSuggestionSerializer(
            suggestion,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _documents_for_request(self, profile, document_ids):
        queryset = CandidateDocument.objects.filter(profile=profile)
        if document_ids:
            return queryset.filter(id__in=document_ids)
        context_documents = queryset.filter(use_for_ai_context=True)
        if context_documents.exists():
            return context_documents
        return queryset
