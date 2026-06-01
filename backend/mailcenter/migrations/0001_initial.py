# Generated for AI Job Application Copilot MVP

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("applications", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmailMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sender", models.EmailField(max_length=254)),
                ("subject", models.CharField(max_length=255)),
                ("body", models.TextField()),
                ("received_at", models.DateTimeField()),
                (
                    "classification",
                    models.CharField(
                        choices=[
                            ("confirmation", "Confirmation"),
                            ("rejection", "Rejection"),
                            ("invitation", "Invitation"),
                            ("question", "Question"),
                            ("follow_up", "Follow-up"),
                            ("unknown", "Unknown"),
                            ("requires_action", "Requires action"),
                        ],
                        default="unknown",
                        max_length=40,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "application",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="emails",
                        to="applications.application",
                    ),
                ),
            ],
            options={"ordering": ["-received_at", "-created_at"]},
        ),
    ]
