# Generated by Django 3.2.16 on 2024-01-04 11:07

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("seo", "0003_remove_attributepair_tag"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="attributepair",
            unique_together={("attribute_name", "attribute_value")},
        ),
    ]