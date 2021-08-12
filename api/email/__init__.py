from django.conf import settings
from .common import TEMPLATES
from .gsuite import GsuiteEmailBuilder
from .sendgrid import SendgridEmailBuilder


email_builder = {
    "backends.gsuite.GSuiteEmailBackend": GsuiteEmailBuilder,
    "backends.sendgrid.SendgridEmailBackend": SendgridEmailBuilder,
}[getattr(settings, "EMAIL_BACKEND")]()

email_trigger = email_builder.build

__all__ = ["email_trigger", "TEMPLATES"]
