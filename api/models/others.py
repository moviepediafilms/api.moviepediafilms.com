from django.db import models
from api.models import Profile


class Notification(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="notifications"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.URLField(null=True, blank=True)
