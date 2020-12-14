from logging import getLogger
from django.db import models
from django.contrib.auth.models import User
from api.constants import GENDER
from api.emails import email_trigger, TEMPLATES

logger = getLogger("api.model")


class Role(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Profile(models.Model):
    GENDER_CHOICES = (
        (GENDER.MALE, "Male"),
        (GENDER.FEMALE, "Female"),
        (GENDER.OTHERS, "Others"),
    )
    onboarded = models.BooleanField(default=True)
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
    roles = models.ManyToManyField("Role", blank=True, related_name="profiles")
    image = models.URLField(null=True, blank=True)
    follows = models.ManyToManyField("Profile", blank=True, related_name="followed_by")
    is_celeb = models.BooleanField(default=False)

    # content consumers attributes
    mcoins = models.FloatField(default=0)
    # will get updated after a defined interval of time
    rank = models.IntegerField(default=-1)
    level = models.IntegerField(default=1)

    watchlist = models.ManyToManyField(
        "Movie", blank=True, related_name="watchlisted_by"
    )

    # content creators attributes
    pop_score = models.FloatField(default=0)

    # content consumers attributes
    engagement_score = models.FloatField(default=0)

    # TODO: update via signals
    # cached
    reviews_given = models.IntegerField(default=0)

    titles = models.ManyToManyField("Title", blank=True, related_name="title_holders")

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        profile = self
        new_onboarding = profile.id is None and profile.onboarded
        old_onboarding = (
            profile.id
            and not Profile.objects.get(pk=profile.id).onboarded
            and profile.onboarded
        )
        if new_onboarding or old_onboarding:
            logger.info(f"new user onboarded! {profile.user.email}")
            email_trigger(profile.user, TEMPLATES.WELCOME)
            logger.info("welcome email sent")
            email_trigger(profile.user, TEMPLATES.VERIFY)
            logger.info("verification email sent")
