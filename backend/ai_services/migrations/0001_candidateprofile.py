from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CandidateProfile",
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
                ("full_name", models.CharField(blank=True, max_length=160)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("location", models.CharField(blank=True, max_length=160)),
                ("target_roles", models.JSONField(blank=True, default=list)),
                ("preferred_locations", models.JSONField(blank=True, default=list)),
                ("remote_preference", models.CharField(blank=True, max_length=120)),
                ("salary_expectation", models.CharField(blank=True, max_length=120)),
                ("availability", models.CharField(blank=True, max_length=160)),
                ("skills", models.JSONField(blank=True, default=list)),
                ("tech_stack", models.JSONField(blank=True, default=list)),
                ("projects", models.JSONField(blank=True, default=list)),
                ("experience_summary", models.TextField(blank=True)),
                ("education_summary", models.TextField(blank=True)),
                ("strengths", models.JSONField(blank=True, default=list)),
                ("no_gos", models.JSONField(blank=True, default=list)),
                ("application_tone", models.CharField(blank=True, max_length=160)),
                ("extra_context", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["id"],
            },
        ),
    ]
