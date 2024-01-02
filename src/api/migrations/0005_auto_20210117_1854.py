# Generated by Django 3.1.4 on 2021-01-17 13:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0004_auto_20210115_2345"),
    ]

    operations = [
        migrations.CreateModel(
            name="MpGenre",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50, unique=True)),
                ("live", models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name="movie",
            name="mp_genres",
            field=models.ManyToManyField(related_name="movies", to="api.MpGenre"),
        ),
    ]
