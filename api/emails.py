from rest_framework.authtoken.models import Token
from django.core.mail import EmailMessage

# name
WELCOME_MAIL_TEMPLATE = "d-a7a0fd0e3fe84e13bae1625541d2db35"
# token
VERIFY_EMAIL_TEMPLATE = "d-a2bf40cdabb3430db9836934beb2ab68"
# name, token
PASSWORD_REST_TEMPLATE = "d-06e58c74df7f43a787511fefff9a06b6"


def get_welcome_mail(profile):
    return build_email(
        [profile.user.email],
        template_id=WELCOME_MAIL_TEMPLATE,
        template_data={"user": profile.user.get_full_name()},
    )


def get_email_verification_mail(profile):
    token, _ = Token.objects.get_or_create(user=profile.user)
    return build_email(
        [profile.user.email],
        template_id=VERIFY_EMAIL_TEMPLATE,
        template_data={"token": token.key},
    )


def get_password_reset_mail(user):
    token, _ = Token.objects.get_or_create(user=user)
    return build_email(
        [user.email],
        template_id=PASSWORD_REST_TEMPLATE,
        template_data={"token": token.key, "name": user.get_full_name()},
    )


def build_email(to, subject=None, body=None, template_id=None, template_data=None):
    email = EmailMessage(subject, body, to=to,)
    if template_id:
        email.template_id = template_id
    if template_data:
        email.template_data = template_data
    return email
