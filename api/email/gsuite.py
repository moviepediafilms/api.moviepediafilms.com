import logging
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.exceptions import ImproperlyConfigured
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .common import (
    TemplateVariables,
    template_variables_map,
    TEMPLATES,
    BaseEmailBuilder,
)

logger = logging.getLogger("gsuite")


gsuite_template_map = {
    TEMPLATES.WELCOME_MDFF: "welcome_mdff2.html",
    TEMPLATES.VERIFY: "email_verify.html",
    TEMPLATES.PASSWORD_RESET: "password_reset.html",
    TEMPLATES.DIRECTOR_APPROVAL: "director_approval.html",
    TEMPLATES.SUBMIT_CONFIRM_DIRECTOR: "submit_confirm_director.html",
    TEMPLATES.SUBMIT_CONFIRM_CREW: "submit_confirm_crew.html",
}


class GsuiteEmailBuilder(BaseEmailBuilder):
    def __init__(self):
        template_dir = getattr(settings, "EMAIL_TEMPLATE_FOLDER")
        self.env = Environment(
            loader=FileSystemLoader(template_dir), autoescape=select_autoescape()
        )

    def get_template(self, template_name, context):
        template = self.env.get_template(template_name)
        return template.render(context)

    # all build should have same signature
    def build(self, user, template_id, fail_silently=False, **kwargs):
        if "user" not in kwargs:
            kwargs["user"] = user
        args_needed = template_variables_map[template_id]

        values = TemplateVariables(**kwargs)
        context = {arg: getattr(values, arg) for arg in args_needed}
        template_name = gsuite_template_map[template_id]
        content = self.get_template(template_name, context)
        if content.count("\n") == 0:
            logger.warn(f"no subject specified for template {template_id}")
            subject = "Moviepedia Films"
            body = content
        else:
            subject, body = content.split("\n", 1)
        email = EmailMessage(subject=subject, to=[user.email], body=body)
        # for unittest test
        email.template_id = template_id
        return email.send(fail_silently=fail_silently)
