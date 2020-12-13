from logging import getLogger
from django.db.models.signals import post_save
from django.dispatch import receiver
from api.models import Profile
from api.emails import email_trigger, TEMPLATES
from api.decorators import ignore_raw

logger = getLogger("api.signals")


@receiver(post_save, sender=Profile)
@ignore_raw
def on_user_registration(sender, **kwargs):
    if kwargs.get("created"):
        profile = kwargs.get("instance")
        logger.info(f"new user registered! {profile.user.email}")
        email_trigger(profile.user, TEMPLATES.WELCOME)
        email_trigger(profile.user, TEMPLATES.VERIFY)
