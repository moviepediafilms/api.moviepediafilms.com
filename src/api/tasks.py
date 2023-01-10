from moviepedia import celery_app
from django.core.management import call_command
from api.models.movie import Movie
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def run_management(self, name):
    if name in [
        "updateengagementscore",
        "updatepopscore",
        "updateroles",
        "updatetopcreators",
        "updatetopcurators",
        "updatemovierecommends",
        "youtubelinkfix",
    ]:
        call_command(name)


@celery_app.task(bind=True)
def queue_movies_for_thumb_generation(self):
    movie_ids = Movie.objects.exclude(
        poster__isnull=False, poster_thumb__isnull=True
    ).values_list("id", flat=True)
    logger.info(len(movie_ids), "without thumbnails")
    for movie_id in movie_ids:
        create_poster_thumb.delay(movie_id)


@celery_app.task(bind=True)
def create_poster_thumb(self, movie_id):
    call_command("generate-poster-thumbs", movie_id=movie_id, overwrite=True)
