# Generated by Django 3.2.16 on 2024-01-01 21:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0020_movie_extras"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="movie",
            name="extras",
        ),
        migrations.AddField(
            model_name="order",
            name="extras",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
