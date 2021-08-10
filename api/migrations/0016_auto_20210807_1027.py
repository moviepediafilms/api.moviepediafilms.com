# Generated by Django 3.2.6 on 2021-08-07 04:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0015_auto_20210807_1020"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="movie",
            name="order",
        ),
        migrations.RemoveField(
            model_name="movie",
            name="package",
        ),
        migrations.AddField(
            model_name="order",
            name="movies",
            field=models.ManyToManyField(to="api.Movie"),
        ),
    ]
