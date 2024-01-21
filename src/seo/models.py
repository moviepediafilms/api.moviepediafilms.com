from django.db import models
from django.contrib.contenttypes.models import ContentType


class Page(models.Model):
    url = models.CharField(max_length=255, unique=True)
    is_pattern = models.BooleanField(default=False)
    model_pk = models.CharField(max_length=255, blank=True, null=True)
    models_to_select = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        limit_choices_to={"app_label": "api"},
    )
    tags = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.url

    def save(self, *args, **kwargs):
        """don't allow page starting with /admin to be created"""
        if self.url.startswith("/admin"):
            raise ValueError("Page URL cannot start with /admin")
        super().save(*args, **kwargs)


class MetaValue(models.Model):
    name = models.CharField(max_length=255)
    value = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
