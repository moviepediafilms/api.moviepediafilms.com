from django.db import models
from django.contrib.auth.models import User
from api.constants import CLAIM_STATE

CLAIM_STATE_CHOICES = (
    (CLAIM_STATE.CREATED, "Created"),
    (CLAIM_STATE.SUCCESS, "Success"),
    (CLAIM_STATE.FAILED, "Failed"),
)


class BadgeClaim(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.FloatField()
    state = models.CharField(max_length=1, choices=CLAIM_STATE_CHOICES)


class Judge(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    about = models.TextField()
    recom_movies = models.ManyToManyField("Movie")


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movies = models.ManyToManyField("Movie")


class Badge(models.Model):
    name = models.CharField(max_length=30)
    icon = models.URLField()


class GameAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey("Movie", on_delete=models.CASCADE)
    selected_frames = models.ManyToManyField("MovieFrame")
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(null=True, blank=True)
    multiplier = models.FloatField()
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)


class Notification(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class AwardType(models.Model):
    name = models.CharField(max_length=20)


class Award(models.Model):
    awarded_at = models.DateTimeField()
    type = models.ForeignKey(AwardType, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey("Movie", blank=True, null=True, on_delete=models.CASCADE)
