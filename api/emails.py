from rest_framework.authtoken.models import Token
from django.core.mail import EmailMessage
from django.conf import settings
import os
import logging

logger = logging.getLogger("api.emails")

# sendgrid
# class TEMPLATES:
#     """SendGrid dynamic email templates used"""

#     WELCOME = "d-a7a0fd0e3fe84e13bae1625541d2db35"
#     VERIFY = "d-a2bf40cdabb3430db9836934beb2ab68"
#     PASSWORD_RESET = "d-06e58c74df7f43a787511fefff9a06b6"
#     DIRECTOR_APPROVAL = "d-f7a6a234d110411ea140e9a43fcd3fe8"
#     SUBMIT_CONFIRM_DIRECTOR = "d-a2b26474eff54ca98154f1ac24cae8c0"
#     SUBMIT_CONFIRM_CREW = "d-9937bf56a2a34301ab7ae37a94bc5a0c"


class TEMPLATES:
    """Gsuite SMTP"""

    WELCOME = "welcome.html"
    VERIFY = "verify.html"
    PASSWORD_RESET = "password_reset.html"
    DIRECTOR_APPROVAL = "director_approval.html"
    SUBMIT_CONFIRM_DIRECTOR = "submit_confirm_director.html"
    SUBMIT_CONFIRM_CREW = "submit_confirm_crew.html"


template_register = {
    TEMPLATES.WELCOME: ("user",),
    TEMPLATES.VERIFY: ("token",),
    TEMPLATES.PASSWORD_RESET: ("name", "token"),
    TEMPLATES.DIRECTOR_APPROVAL: ("profile_aware_link",),
    TEMPLATES.SUBMIT_CONFIRM_DIRECTOR: ("user",),
    TEMPLATES.SUBMIT_CONFIRM_CREW: ("user",),
}


class TemplateVariables:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @property
    def user(self):
        return self.name

    @property
    def name(self):
        user = self.kwargs["user"]
        return user.get_full_name()

    @property
    def token(self):
        user = self.kwargs["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return token.key

    @property
    def profile_aware_link(self):
        """If profile is complete the link should point to notification page, otherwise to signup page"""

        user = self.kwargs["user"]
        if user.is_active:
            # the director profile is not complete, send link to complete the profile
            return f"sign-up?token={self.token}&email={user.email}&id={user.profile.id}"
        return "notification"


# sendgrid
# def email_trigger(user, template_id, fail_silently=False, **kwargs):
#     if "user" not in kwargs:
#         kwargs["user"] = user
#     args_needed = template_register[template_id]
#     template_variables = TemplateVariables(**kwargs)
#     template_data = {arg: getattr(template_variables, arg) for arg in args_needed}
#     email = build_email(
#         to=[user.email], template_id=template_id, template_data=template_data
#     )
#     return email.send(fail_silently=fail_silently)

# SMTP GSUITE
def email_trigger(user, template_id, fail_silently=True, **kwargs):
    if "user" not in kwargs:
        kwargs["user"] = user
    args_needed = template_register[template_id]
    template_dir = getattr(settings, "EMAIL_TEMPLATE_FOLDER")
    try:
        with open(os.path.join(template_dir, template_id), "r") as f:
            content = f.read()
    except Exception as ex:
        logging.exception(ex)
        print(ex)
    else:
        template_variables = TemplateVariables(**kwargs)
        template_data = {arg: getattr(template_variables, arg) for arg in args_needed}
        content = content.format(**template_data)
        if content.count("\n") == 0:
            logger.warn(f"no subject specified for template {template_id}")
            subject = template_id
            body = content
        else:
            subject, body = content.split("\n", 1)
        email = build_email(subject=subject, to=[user.email], body=body)
        return email.send(fail_silently=fail_silently)


def build_email(to, subject=None, body=None, template_id=None, template_data=None):
    email = EmailMessage(
        subject,
        body,
        to=to,
    )
    if template_id:
        email.template_id = template_id
    if template_data:
        email.template_data = template_data
    return email
