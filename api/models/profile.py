from logging import getLogger
from django.db import models
from django.contrib.auth.models import User
from api.constants import GENDER
from api.email import email_trigger, TEMPLATES

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
    celeb_order = models.IntegerField(default=0)

    # content consumers attributes
    mcoins = models.FloatField(default=0)
    # cached, will get updated by updatetopcurator job
    curator_rank = models.IntegerField(default=-1)
    # cached, will get updated by updatetopcreator job
    creator_rank = models.IntegerField(default=-1)

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
        is_new = self.id is None
        new_onboarding = is_new and self.onboarded
        old_onboarding = (
            not is_new
            and not Profile.objects.get(pk=self.id).onboarded
            and self.onboarded
        )
        super().save(*args, **kwargs)

        logger.info(f"new_onboarding/old_onboarding: {new_onboarding}/{old_onboarding}")
        if new_onboarding or old_onboarding:
            logger.info(f"user onboarded! {self.user.email}")
            # disabling welcome emails
            # success = email_trigger(self.user, TEMPLATES.WELCOME)
            # logger.info(f"welcome email sent: {success}")
            success = email_trigger(self.user, TEMPLATES.VERIFY)
            logger.info(f"verification email sent: {success}")
