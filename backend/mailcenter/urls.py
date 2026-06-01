from django.urls import path

from .views import sync_mail


urlpatterns = [
    path("sync/", sync_mail, name="mail-sync"),
]
