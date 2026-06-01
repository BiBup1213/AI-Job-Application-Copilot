# Generated for AI Job Application Copilot MVP

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("jobs", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Application",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("new", "New"),
                            ("interesting", "Interesting"),
                            ("draft_open", "Draft open"),
                            ("draft_approved", "Draft approved"),
                            ("gmail_draft_created", "Gmail draft created"),
                            ("applied", "Applied"),
                            ("response_received", "Response received"),
                            ("interview", "Interview"),
                            ("rejected", "Rejected"),
                            ("follow_up_due", "Follow-up due"),
                            ("closed", "Closed"),
                        ],
                        default="new",
                        max_length=40,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("applied_at", models.DateTimeField(blank=True, null=True)),
                ("follow_up_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "job",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="applications",
                        to="jobs.jobposting",
                    ),
                ),
            ],
            options={"ordering": ["-updated_at", "-created_at"]},
        ),
        migrations.CreateModel(
            name="ApplicationDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "document_type",
                    models.CharField(
                        choices=[
                            ("cover_letter", "Cover letter"),
                            ("email", "Email"),
                            ("follow_up", "Follow-up"),
                            ("reply", "Reply"),
                        ],
                        max_length=40,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("content", models.TextField()),
                ("version", models.PositiveIntegerField(default=1)),
                ("is_approved", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="documents",
                        to="applications.application",
                    ),
                ),
            ],
            options={
                "ordering": ["application", "document_type", "-version"],
                "unique_together": {("application", "document_type", "version")},
            },
        ),
        migrations.CreateModel(
            name="StatusEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("old_status", models.CharField(blank=True, max_length=40)),
                ("new_status", models.CharField(max_length=40)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_events",
                        to="applications.application",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
