from logging import getLogger

from django.core.management.base import BaseCommand
from api.models import User, Movie
from api.email import TEMPLATES, email_trigger


logger = getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            help="email address to send all test emails to",
            type=str,
            required=True,
        )
        parser.add_argument(
            "--all",
            help="send all type of emails",
            action="store_true",
        )

    def handle(self, *args, **options):
        email = options["email"]
        send_all = options.get("all")
        zee = User.objects.get(email=email)
        movie = Movie.objects.first()
        for attr in dir(TEMPLATES):
            if not attr.startswith("_"):
                logger.info(f"sending {attr} email")
                email_trigger(zee, getattr(TEMPLATES, attr), False, movie=movie)
                if not send_all:
                    break
