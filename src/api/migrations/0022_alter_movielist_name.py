# Generated by Django 3.2.16 on 2024-01-17 05:04

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0021_auto_20240102_0252"),
    ]

    operations = [
        migrations.AlterField(
            model_name="movielist",
            name="name",
            field=models.CharField(max_length=100),
        ),
    ]