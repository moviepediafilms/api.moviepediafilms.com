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
            "--movie-id",
            help="movie id to generate thumb for",
            type=int,
            required=True,
        )
        parser.add_argument(
            "--all", help="do it for all movies", type=bool, default=False
        )
        parser.add_argument(
            "--overwrite", help="overwrite existing thumb", type=bool, default=False
        )

    def handle(self, *args, **options):
        format = "webp"
        movie_id = options["movie_id"]
        for_all = options["all"]
        overwrite = options["overwrite"]

        movie = Movie.objects.get(id=movie_id)
        movies = (
            [movie] if not for_all else Movie.objects.exclude(poster__isnull=True).all()
        )
        for movie in movies:
            base_poster_thumbs_path = os.path.join(settings.MEDIA_POSTERS, "thumbs")

            if movie.poster_thumb is not None and not overwrite:
                logger.info(f"{movie.title} already has thumbs at {movie.poster_thumb}")
                continue

            thumb_filename = f"{movie.id:010d}.{format}"
            if not default_storage.exists(movie.poster):
                logger.error(f"poster missing '{movie.title}' {movie.poster}")
                continue

            thumb_path = os.path.join(base_poster_thumbs_path, thumb_filename)
            logger.info(f"thumbnail saving at {thumb_path}")

            try:
                poster_fh = default_storage.open(movie.poster)
                with Image.open(poster_fh) as image:
                    image.thumbnail(settings.POSTER_THUMB_DIMENS)

                    thumb_fh = default_storage.open(thumb_path, "wb")
                    image.save(thumb_fh, format)
                    thumb_fh.close()

                    movie.poster_thumb = default_storage.url(thumb_path)
                    movie.save()
                poster_fh.close()
            except Exception:
                logger.exception("failed to generate thumb")
