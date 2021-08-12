import base64
import threading

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import sanitize_address
from google.auth import exceptions
from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from .utils import get_credentials_file
import logging

logger = logging.getLogger("gsuite")


class GSuiteEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        self.fail_silently = fail_silently
        self.credentials = get_credentials_file()
        self.API_SCOPE = [
            "https://www.googleapis.com/auth/gmail.send",
        ]
        # to reopen connection with different delegation when from_email changes
        self.current_user = None
        self.connection = None
        self._lock = threading.RLock()

    def _delegate_user(self, user_id):
        credentials = service_account.Credentials.from_service_account_file(
            self.credentials, scopes=self.API_SCOPE
        )
        credentials_delegated = credentials.with_subject(user_id)
        return credentials_delegated

    def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects and return the number of email
        messages sent.
        """
        if not email_messages:
            return 0
        with self._lock:
            num_sent = 0
            for message in email_messages:
                # maybe sanitize this message.from_email?
                new_conn_created = self.open(from_email=message.from_email)
                if not self.connection or new_conn_created is None:
                    logger.warning(f"No connection, skipping email {message}")
                    continue
                sent = self._send(message)
                if sent:
                    num_sent += 1
        return num_sent

    def open(self, from_email):
        """
        Ensure an open connection to the email server. Return whether or not a
        new connection was required (True or False) or None if an exception
        passed silently.
        """
        if not self.current_user:
            self.current_user = from_email
            logger.debug(f"setting current_user to {from_email}")

        if self.connection and from_email == self.current_user:
            logger.debug(f"connection already exists with user {from_email}")
            return False

        try:
            logger.debug(f"creating a new connection {from_email}")
            credentials = self._delegate_user(from_email)
            self.connection = build("gmail", "v1", credentials=credentials)
            self.current_user = from_email
            return True
        except (
            exceptions.DefaultCredentialsError,
            exceptions.GoogleAuthError,
            exceptions.RefreshError,
            exceptions.TransportError,
        ):
            if not self.fail_silently:
                raise

    def close(self):
        """Close the connection to the email server."""
        if self.connection is None:
            return
        # do something
        return

    def _send(self, email_message):
        """A helper method that does the actual sending."""
        if not email_message.recipients():
            return False
        encoding = email_message.encoding or settings.DEFAULT_CHARSET
        # check this
        from_email = sanitize_address(email_message.from_email, encoding)
        recipients = [
            sanitize_address(addr, encoding) for addr in email_message.recipients()
        ]
        msg = MIMEMultipart("alternative")
        msg["subject"] = email_message.subject
        msg["from"] = from_email
        msg["to"] = recipients[0]
        # msg.attach(MIMEText(msgPlain, "plain"))
        msg.attach(MIMEText(email_message.body, "html"))
        raw = base64.urlsafe_b64encode(msg.as_bytes())
        raw = raw.decode()
        binary_content = {"raw": raw}
        try:
            # need different login to check success
            self.connection.users().messages().send(
                userId="me", body=binary_content
            ).execute()
        except (
            exceptions.DefaultCredentialsError,
            exceptions.GoogleAuthError,
            exceptions.RefreshError,
            exceptions.TransportError,
        ):
            if not self.fail_silently:
                raise
            return False
        return True
