# Generated by Django 3.1.4 on 2020-12-26 13:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="profile",
            old_name="rank",
            new_name="creator_rank",
        ),
        migrations.AddField(
            model_name="profile",
            name="curator_rank",
            field=models.IntegerField(default=-1),
        ),
        migrations.AlterField(
            model_name="movie",
            name="about",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="movie",
            name="contest",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="movies",
                to="api.contest",
            ),
        ),
        migrations.AlterField(
            model_name="movie",
            name="lang",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="api.movielanguage",
            ),
        ),
    ]
