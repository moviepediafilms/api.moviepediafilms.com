from logging import getLogger
from django.db.models.signals import post_save
from django.dispatch import receiver
from api.models import Profile
from api.emails import get_welcome_mail, get_email_verification_mail

logger = getLogger("api.signals")


@receiver(post_save, sender=Profile)
def on_user_registration(sender, **kwargs):
    profile = kwargs.get("instance")
    if kwargs.get("raw"):
        # skip if triggered by loaddata
        return
    if kwargs.get("created"):
        logger.info(f"new user registered! {profile.user.email}")
        for mail in [get_welcome_mail(profile), get_email_verification_mail(profile)]:
            mail.send()
