from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from ai_services.services import classify_email_message, sync_mock_email_messages

from .models import EmailMessage
from .serializers import EmailMessageSerializer


class EmailMessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EmailMessage.objects.select_related("application", "application__job").all()
    serializer_class = EmailMessageSerializer

    @action(detail=True, methods=["post"], url_path="classify")
    def classify(self, request, pk=None):
        email = self.get_object()
        classify_email_message(email)
        return Response(EmailMessageSerializer(email).data)


@api_view(["POST"])
def sync_mail(request):
    messages = sync_mock_email_messages()
    return Response(
        {
            "message": "Mock-Mail-Sync abgeschlossen. Es wurde keine Gmail API aufgerufen.",
            "created_messages": len(messages),
            "message_ids": [message.id for message in messages],
        },
        status=status.HTTP_201_CREATED,
    )
