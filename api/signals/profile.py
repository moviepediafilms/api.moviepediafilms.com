from logging import getLogger
from django.db.models.signals import pre_save
from django.dispatch import receiver
from api.models import Profile
from api.emails import email_trigger, TEMPLATES
from api.decorators import ignore_raw

logger = getLogger("api.signals")


@receiver(pre_save, sender=Profile)
@ignore_raw
def on_user_registration(sender, **kwargs):
    profile = kwargs.get("instance")
    new_onboarding = profile.id is None and profile.onboarded
    old_onboarding = (
        profile.id
        and not Profile.object.get(profile.id).onboarded
        and profile.onboarded
    )
    if new_onboarding or old_onboarding:
        logger.info(f"new user onboarded! {profile.user.email}")
        email_trigger(profile.user, TEMPLATES.WELCOME)
        logger.info("welcome email sent")
        email_trigger(profile.user, TEMPLATES.VERIFY)
        logger.info("verification email sent")
