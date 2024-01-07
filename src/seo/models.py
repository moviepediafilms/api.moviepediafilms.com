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
