import re
from django.db.models import Q
from django.core.management.base import BaseCommand
from api.models import Movie
from api.constants import MOVIE_STATE
from logging import getLogger

logger = getLogger(__name__)
# Patterns to capture youtube video ID, (pattern, group at which the id is captures)
video_id_patterns = [(r"youtu.be/(.+)", 1), (r"watch\?v=(.+?)(?=(&|$))", 1)]


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="show the changed URL without making any changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        for movie in Movie.objects.filter(
            Q(state=MOVIE_STATE.SUBMITTED) | Q(state=MOVIE_STATE.PUBLISHED)
        ).all():
            try:
                if self.is_youtube_link(movie.link):
                    fixed_link = self.convert_to_embedded(movie.link)
                    logger.debug(f"{movie.link} => {fixed_link}")
                    if not dry_run and fixed_link and fixed_link != movie.link:
                        movie.link = fixed_link
                        movie.save()
            except Exception as ex:
                logger.error(f"error fixing link for {movie.link}")
                logger.exception(ex)

    def is_youtube_link(self, url):
        return bool(re.search(r"youtu(\.be|be.com)", url))

    def convert_to_embedded(self, url):
        for pattern, video_id_group in video_id_patterns:
            match = re.search(pattern, url)
            if match:
                ytb_movie_id = match.group(video_id_group)
                return f"https://www.youtube.com/embed/{ytb_movie_id}"
        logger.warn(f"failed to find video ID from youtube link {url}")
        return url
