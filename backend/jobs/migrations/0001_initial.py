# Generated for AI Job Application Copilot MVP

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="JobPosting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("company", models.CharField(max_length=255)),
                ("title", models.CharField(max_length=255)),
                ("location", models.CharField(blank=True, max_length=255)),
                ("source", models.CharField(blank=True, max_length=120)),
                ("source_url", models.URLField(blank=True)),
                ("description", models.TextField(blank=True)),
                ("requirements", models.JSONField(blank=True, default=list)),
                ("nice_to_have", models.JSONField(blank=True, default=list)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("employment_type", models.CharField(blank=True, max_length=80)),
                ("remote_type", models.CharField(blank=True, max_length=80)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-published_at", "-created_at"]},
        ),
        migrations.CreateModel(
            name="JobMatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "score",
                    models.IntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ]
                    ),
                ),
                ("category", models.CharField(choices=[("A", "A"), ("B", "B"), ("C", "C"), ("X", "X")], max_length=1)),
                ("strengths", models.JSONField(blank=True, default=list)),
                ("risks", models.JSONField(blank=True, default=list)),
                ("recommendation", models.TextField(blank=True)),
                ("application_angle", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "job",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="match",
                        to="jobs.jobposting",
                    ),
                ),
            ],
            options={"ordering": ["-score", "-created_at"]},
        ),
    ]
