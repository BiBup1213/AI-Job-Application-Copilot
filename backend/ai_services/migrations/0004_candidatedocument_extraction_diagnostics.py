from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_services", "0003_candidateprofilesuggestion"),
    ]

    operations = [
        migrations.AddField(
            model_name="candidatedocument",
            name="extracted_text_length",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="candidatedocument",
            name="extraction_error",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
