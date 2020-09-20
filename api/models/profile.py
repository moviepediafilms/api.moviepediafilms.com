from django.db import models
from django.contrib.auth.models import User
from api.constants import GENDER

GENDER_CHOICES = (
    (GENDER.MALE, "Male"),
    (GENDER.FEMALE, "Female"),
    (GENDER.OTHERS, "Others"),
)


class ProfileType(models.Model):
    name = models.CharField(max_length=20)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    city = models.CharField(max_length=100)
    mobile = models.CharField(max_length=20)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    dob = models.DateField()
    type = models.ForeignKey(ProfileType, on_delete=models.CASCADE)
    image = models.URLField()
    follows = models.ManyToManyField("Profile", blank=True)

    # content consumers attributes
    mcoins = models.FloatField()
    # will get updated after a defined interval of time
    rank = models.IntegerField()
    # score as per current level
    score = models.FloatField()
    level = models.IntegerField()
    # insert a badge here after the attempt, so that user can claim it
    badges = models.ManyToManyField("Badge")

    # content creators attributes
    pop_score = models.FloatField()
