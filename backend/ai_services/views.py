from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services import dashboard_summary


@api_view(["GET"])
def dashboard_summary_view(request):
    return Response(dashboard_summary())
