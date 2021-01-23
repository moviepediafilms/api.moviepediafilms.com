# Updates Top creators for live contests

from api.constants import MOVIE_STATE, RECOMMENDATION
from api.models import Contest, CrewMember, TopCreator
from django.db import transaction
from django.core.management.base import BaseCommand
from django.utils import timezone
from logging import getLogger

logger = getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        now = timezone.now()
        live_contests = Contest.objects.filter(start__lte=now, end__gte=now).all()
        logger.info(f"Live contests: {len(live_contests)}")
        for contest in live_contests:
            logger.info(f"Contest: {contest.name} with {contest.movies.count()} movies")
            movies_by_director = self._get_movies_by_director(contest)
            logger.info(f"found {len(movies_by_director)} directors")
            top_creators = []
            for director_id, movies in movies_by_director.items():
                top_creator_data = {"profile_id": director_id, "contest_id": contest.id}
                top_creator_data.update(self._get_score(movies))
                top_creators.append(top_creator_data)

            top_creators = sorted(top_creators, key=lambda x: x.get("score", 0))
            top_creators = [
                TopCreator(pos=pos + 1, **data) for pos, data in enumerate(top_creators)
            ]

            logger.info(f"created {len(top_creators)} creator(s)")
            with transaction.atomic():
                old_top_creators = TopCreator.objects.filter(contest=contest)
                logger.info(f"deleting {old_top_creators.count()} creators")
                old_top_creators.delete()
                logger.info(f"adding {len(top_creators)} new creators")
                TopCreator.objects.bulk_create(top_creators, batch_size=100)

    def _get_score(self, movies):
        score = {
            "score": 0,
            "recommend_count": 0,
        }
        avg_jury_rating = round(
            sum(movie.jury_rating or 0 for movie in movies) / len(movies), 2
        )
        avg_audience_rating = round(
            sum(movie.audience_rating or 0 for movie in movies) / len(movies), 2
        )
        sum_of_all_recommendations = sum(
            movie.in_lists.filter(name=RECOMMENDATION).count() for movie in movies
        )

        composite_score = (
            avg_jury_rating * 0.3
            + avg_audience_rating * 0.3
            + min((sum_of_all_recommendations * 0.025), 10)
        )
        score["score"] = round(
            composite_score * 10,
            2,
        )
        score["recommend_count"] = sum_of_all_recommendations
        return score

    def _get_movies_by_director(self, contest):
        movies_by_director = {}
        for movie in contest.movies.filter(state=MOVIE_STATE.PUBLISHED).all():
            directors = self._get_directors(movie)

            for director in directors:
                if director.id not in movies_by_director:
                    movies_by_director[director.id] = []
                movies_by_director[director.id].append(movie)
        return movies_by_director

    def _get_directors(self, movie):
        return [
            dir_role.profile
            for dir_role in CrewMember.objects.filter(
                movie=movie, role__name="Director"
            ).all()
        ]
