from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ai_services", "0002_candidatedocument"),
    ]

    operations = [
        migrations.CreateModel(
            name="CandidateProfileSuggestion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("suggested_data", models.JSONField(blank=True, default=dict)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("applied", "Applied"),
                            ("dismissed", "Dismissed"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("applied_at", models.DateTimeField(blank=True, null=True)),
                (
                    "profile",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="suggestions",
                        to="ai_services.candidateprofile",
                    ),
                ),
                (
                    "source_documents",
                    models.ManyToManyField(
                        blank=True,
                        related_name="profile_suggestions",
                        to="ai_services.candidatedocument",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
