from django.db.models.signals import post_save
from django.dispatch import receiver
from api.models import Profile
from rest_framework.authtoken.models import Token
from django.core.mail import EmailMessage
from logging import getLogger

logger = getLogger("api.signals")

WELCOME_MAIL_TEMPLATE = "d-bfd069c310b74005837737ecda2aeec3"
VERIFY_EMAIL_TEMPLATE = "d-a2bf40cdabb3430db9836934beb2ab68"


def get_welcome_mail(profile):
    return build_email(
        [profile.user.email],
        template_id=WELCOME_MAIL_TEMPLATE,
        substitutions={"user": profile.user.get_full_name()},
    )


def get_email_verification_mail(profile):
    token, _ = Token.objects.get_or_create(user=profile.user)
    print(token.key)
    return build_email(
        [profile.user.email],
        template_id=VERIFY_EMAIL_TEMPLATE,
        substitutions={"token": token.key},
    )


def build_email(to, subject=None, body=None, template_id=None, substitutions=None):
    email = EmailMessage(subject, body, to=to,)
    if template_id:
        email.template_id = template_id
    if substitutions:
        email.substitutions = substitutions
    return email


@receiver(post_save, sender=Profile)
def on_user_registration(sender, **kwargs):
    profile = kwargs.get("instance")
    logger.debug(kwargs)
    logger.debug(sender)
    if kwargs.get("raw"):
        return
    if kwargs.get("created"):
        # send welcome and confirm email to activate account
        logger.info(f"new user registered! {profile.user.email}")
        for mail in [get_welcome_mail(profile), get_email_verification_mail(profile)]:
            mail.send()
