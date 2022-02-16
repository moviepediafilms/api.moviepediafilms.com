from django.utils import timezone
from django.db import models
from django.db.models.deletion import CASCADE
from api.constants import CONTEST_STATE

CONTEST_STATE_CHOICES = [
    (CONTEST_STATE.CREATED, "Created"),
    (CONTEST_STATE.LIVE, "Live"),
    (CONTEST_STATE.FINISHED, "Finished"),
]


class Title(models.Model):
    name = models.CharField(max_length=50)


class ContestWinner(models.Model):
    contest = models.ForeignKey("Contest", on_delete=models.CASCADE)
    profile = models.ForeignKey("Profile", on_delete=models.CASCADE)
    position = models.IntegerField(null=True, blank=True)
    title = models.ForeignKey("Title", on_delete=CASCADE)

    def __str__(self):
        return f"{self.content_id}, {self.profile_id}, {self.position}"


class ContestType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Contest(models.Model):
    name = models.CharField(max_length=100)
    start = models.DateTimeField(auto_now_add=False)
    end = models.DateTimeField(auto_now_add=False)
    days_per_movie = models.IntegerField(default=15)
    type = models.ForeignKey("ContestType", on_delete=models.CASCADE)
    state = models.CharField(
        max_length=1, choices=CONTEST_STATE_CHOICES, default=CONTEST_STATE.CREATED
    )
    winners = models.ManyToManyField("Profile", through="ContestWinner", blank=True)
    max_recommends = models.IntegerField(default=20)

    def __str__(self):
        return self.name

    def is_live(self):
        if self.state == CONTEST_STATE.LIVE:
            now = timezone.now()
            return self.start < now and now < self.end
        else:
            return False
