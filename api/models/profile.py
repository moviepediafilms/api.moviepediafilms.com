from django.db import models
from django.contrib.auth.models import User
from api.constants import GENDER

GENDER_CHOICES = (
    (GENDER.MALE, "Male"),
    (GENDER.FEMALE, "Female"),
    (GENDER.OTHERS, "Others"),
)


class Role(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    about = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    gender = models.CharField(
        max_length=1, choices=GENDER_CHOICES, null=True, blank=True
    )
    dob = models.DateField(null=True, blank=True)
    # cached roles from movie, profile, roles association
    # should be updated as batch process
    roles = models.ManyToManyField("Role", blank=True)
    image = models.URLField(null=True, blank=True)
    follows = models.ManyToManyField("Profile", blank=True)

    # content consumers attributes
    mcoins = models.FloatField(default=0)
    # will get updated after a defined interval of time
    rank = models.IntegerField(default=-1)
    # score as per current level
    score = models.FloatField(default=0)
    level = models.IntegerField(default=1)
    # insert a badge here after the attempt, so that user can claim it
    badges = models.ManyToManyField("Badge", blank=True)

    # content creators attributes
    pop_score = models.FloatField(default=0)
    # fund readiness meter can be derived from pop_score and movie ratings
    recommended = models.ManyToManyField(
        "Movie", blank=True, related_name="recommended_by"
    )
    watchlist = models.ManyToManyField(
        "Movie", blank=True, related_name="watchlisted_by"
    )
