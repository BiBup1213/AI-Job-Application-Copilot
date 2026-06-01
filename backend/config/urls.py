from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from applications.views import ApplicationViewSet
from campaigns.views import SearchCampaignViewSet
from jobs.views import JobPostingViewSet
from mailcenter.views import EmailMessageViewSet


router = DefaultRouter()
router.register("campaigns", SearchCampaignViewSet, basename="campaign")
router.register("jobs", JobPostingViewSet, basename="job")
router.register("applications", ApplicationViewSet, basename="application")
router.register("mail/messages", EmailMessageViewSet, basename="mail-message")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/dashboard/", include("ai_services.dashboard_urls")),
    path("api/mail/", include("mailcenter.urls")),
    path("api/", include(router.urls)),
]
