from django.core.management.base import BaseCommand
from django.db.models import Q
from api.models import Movie
from api.constants import MOVIE_STATE, RECOMMENDATION
from logging import getLogger
import pandas as pd

logger = getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        updates = []
        movies = Movie.objects.filter(state=MOVIE_STATE.PUBLISHED).all()
        for movie in movies:
            recommend_count = movie.in_lists.filter(
                Q(name=RECOMMENDATION) | Q(contest__isnull=False)
            ).count()
            movie.recommend_count = recommend_count
            updates.append(dict(name=movie.title, recommend_count=recommend_count))
        Movie.objects.bulk_update(movies, ["recommend_count"])
        updates.sort(key=lambda x: x["recommend_count"], reverse=True)
        # log top 30 recommended movies
        logger.info(f"recommend count updates: \n{str(pd.DataFrame(updates[:30]))}")
