from django.contrib import admin

from .models import EmailMessage


@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "sender", "application", "classification", "received_at")
    list_filter = ("classification",)
    search_fields = ("sender", "subject", "body", "application__job__company")
