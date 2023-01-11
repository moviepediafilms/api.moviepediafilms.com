from logging import getLogger

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
from api.models import Movie
from PIL import Image
import os

logger = getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--format",
            help="format to convert to",
            default="webp",
            const="webp",
            nargs="?",
            choices=["webp", "png", "jpeg", "jpg"],
            type=str,
        )

    def handle(self, *args, **options):
        format = options["format"]
        for movie in Movie.objects.exclude(poster__isnull=True).all():
            if movie.poster is None:
                logger.info(f"{movie.title} has no poster")
                continue

            if movie.poster.split(".")[-1].lower() == format.lower():
                logger.info(f"{movie.title} already in {format}")
                continue

            newfilename = f"{movie.id:010d}.{format}"
            old_poster = movie.poster
            if not default_storage.exists(old_poster):
                logger.error(f"poster file missing for '{movie.title}' {old_poster}")
                continue

            try:
                image_file = default_storage.open(old_poster)
                with Image.open(image_file) as image:
                    poster_path = os.path.join(settings.MEDIA_POSTERS, newfilename)
                    logger.info(f"new poster saving at {poster_path}")

                    image_fh = default_storage.open(poster_path, "wb")
                    image.save(image_fh, format)
                    image_fh.close()

                    new_poster = default_storage.url(poster_path)
                    movie.poster = new_poster
                    movie.save()
                image_file.close()
                if old_poster != new_poster:
                    logger.info(f"deleting {old_poster}")
                    default_storage.delete(old_poster)
            except Exception as ex:
                logger.exception(ex)
