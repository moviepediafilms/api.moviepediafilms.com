# Generated by Django 3.1.7 on 2021-03-21 14:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0012_profile_celeb_order"),
    ]

    operations = [
        migrations.CreateModel(
            name="PackageAttribute",
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
            ],
        ),
        migrations.AddField(
            model_name="order",
            name="package",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="api.package",
            ),
        ),
        migrations.AddField(
            model_name="package",
            name="active",
            field=models.BooleanField(default=True),
        ),
        migrations.CreateModel(
            name="Release",
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
                ("on", models.DateTimeField(auto_now_add=True)),
                (
                    "contest",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="api.contest"
                    ),
                ),
                (
                    "movie",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="api.movie"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PackageAttributeValue",
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
                ("value", models.CharField(max_length=100)),
                (
                    "attribute",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="value",
                        to="api.packageattribute",
                    ),
                ),
                (
                    "package",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="api.package"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="package",
            name="attributes",
            field=models.ManyToManyField(
                through="api.PackageAttributeValue", to="api.PackageAttribute"
            ),
        ),
    ]
