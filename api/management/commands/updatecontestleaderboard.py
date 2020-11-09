from django.core.management.base import BaseCommand
from logging import getLogger

logger = getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Update")
