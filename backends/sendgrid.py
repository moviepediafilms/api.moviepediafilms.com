from logging import getLogger
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from email.utils import parseaddr
import sendgrid

logger = getLogger("api.mail")


class SendgridEmailBackend(BaseEmailBackend):
    # some of the code is borrowed from https://github.com/elbuo8/sendgrid-django,
    # reason to rewrite this is they are not using the newer JSON based sendgrid API

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        if "api_key" in kwargs:
            self.api_key = kwargs["api_key"]
        else:
            self.api_key = getattr(settings, "SENDGRID_API_KEY", None)
        if not self.api_key:
            raise ImproperlyConfigured(
                """
                SENDGRID_API_KEY must be declared in settings.py"""
            )
        self.sg = sendgrid.SendGridAPIClient(api_key=self.api_key)
        self.dry_run = not getattr(settings, "EMAIL_DISABLED", False)
        logger.info(
            f"sendgrid initialized with key: {bool(self.api_key)} and dry_run: {self.dry_run}"
        )

    def send_messages(self, emails):
        if not emails:
            return

        count = 0
        for email in emails:
            sg_mail = self._build_sg_mail(email)
            try:
                logger.debug(f"sending mail {sg_mail}")
                if self.dry_run:
                    logger.debug("mail not sent! it was a dry run")
                else:
                    self.sg.client.mail.send.post(request_body=sg_mail)
                count += 1
            except Exception as ex:
                logger.error(
                    f"Sendgrid error: {getattr(ex, 'body', b'<no-content>').decode()}"
                )
                if not self.fail_silently:
                    raise
        return count

    def _build_sg_mail(self, email):
        personalization = {}
        sendgrid_mail = {}

        if email.from_email:
            sendgrid_mail["from"] = self._process_email_addr(email.from_email)
        if email.subject:
            sendgrid_mail["subject"] = (email.subject,)
        if email.to:
            personalization["to"] = [self._process_email_addr(e) for e in email.to]
        if email.cc:
            personalization["cc"] = [self._process_email_addr(e) for e in email.cc]
        if email.bcc:
            personalization["bcc"] = [self._process_email_addr(e) for e in email.bcc]
        if email.reply_to:
            sendgrid_mail["reply_to"] = self._process_email_addr(email.reply_to)

        if hasattr(email, "template_id"):
            sendgrid_mail["template_id"] = email.template_id
            if hasattr(email, "template_data"):
                personalization["dynamic_template_data"] = dict(email.template_data)
        if personalization:
            sendgrid_mail["personalizations"] = [personalization]
        return sendgrid_mail

    def _process_email_addr(self, email_addr):
        from_name, from_email = parseaddr(email_addr)
        return {"email": from_email, "name": from_name}
