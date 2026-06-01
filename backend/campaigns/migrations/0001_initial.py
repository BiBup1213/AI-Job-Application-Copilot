# Generated for AI Job Application Copilot MVP

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SearchCampaign",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("keywords", models.JSONField(blank=True, default=list)),
                ("industries", models.JSONField(blank=True, default=list)),
                ("sources", models.JSONField(blank=True, default=list)),
                ("location", models.CharField(blank=True, max_length=255)),
                ("radius_km", models.PositiveIntegerField(default=25)),
                ("remote_allowed", models.BooleanField(default=True)),
                ("hybrid_allowed", models.BooleanField(default=True)),
                ("exclude_keywords", models.JSONField(blank=True, default=list)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("active", "Active"),
                            ("paused", "Paused"),
                            ("completed", "Completed"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
