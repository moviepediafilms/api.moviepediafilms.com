from django.core.mail import EmailMessage
from .common import (
    template_variables_map,
    TemplateVariables,
    TEMPLATES,
    BaseEmailBuilder,
)

sendgrid_template_map = {
    # templates will be outdated no sendgrid
    # {user} -> {name}
    # TEMPLATES.WELCOME: "d-a7a0fd0e3fe84e13bae1625541d2db35",
    TEMPLATES.VERIFY: "d-a2bf40cdabb3430db9836934beb2ab68",
    TEMPLATES.PASSWORD_RESET: "d-06e58c74df7f43a787511fefff9a06b6",
    TEMPLATES.DIRECTOR_APPROVAL: "d-f7a6a234d110411ea140e9a43fcd3fe8",
    TEMPLATES.SUBMIT_CONFIRM_DIRECTOR: "d-a2b26474eff54ca98154f1ac24cae8c0",
    TEMPLATES.SUBMIT_CONFIRM_CREW: "d-9937bf56a2a34301ab7ae37a94bc5a0c",
}


class SendgridEmailBuilder(BaseEmailBuilder):
    def build(user, template_id, fail_silently=False, **kwargs):
        if "user" not in kwargs:
            kwargs["user"] = user
        args_needed = template_variables_map[template_id]
        values = TemplateVariables(**kwargs)
        template_data = {arg: getattr(values, arg) for arg in args_needed}

        email = EmailMessage(to=[user.email])
        if template_id:
            email.template_id = template_id
        if template_data:
            email.template_data = template_data
        return email.send(fail_silently=fail_silently)
