# Updates Top creators for live contests
from collections import defaultdict
from api.constants import MOVIE_STATE
from api.models import Contest, CrewMember, TopCreator
from django.db import transaction
from django.core.management.base import BaseCommand
from django.utils import timezone
from logging import getLogger
import pandas as pd

logger = getLogger(__name__)

MAX_AUDIENCE_RATINGS = 40


class Command(BaseCommand):
    def handle(self, *args, **options):

        top_creator_comparator = lambda x: (  # noqa: E731
            x.get("score", 0),
            x.get("name"),
        )
        now = timezone.now()
        live_contests = Contest.objects.filter(start__lte=now, end__gte=now).all()
        logger.info(f"Live contests: {len(live_contests)}")
        for contest in live_contests:
            logger.info(f"Contest: {contest.name} with {contest.movies.count()} movies")
            movies_by_director = self._get_movies_by_director(contest)
            logger.info(f"found {len(movies_by_director)} directors")
            top_creators = []
            # for logging only
            score_details = []
            for director, movies in movies_by_director.items():
                top_creator_data = {
                    "profile_id": director.id,
                    "contest_id": contest.id,
                    # name used for seconds order sorting
                    "name": director.user.get_full_name(),
                }
                logger.debug(f"for {director}")
                score, detail = self._get_score(movies, contest)
                top_creator_data.update(score)
                top_creators.append(top_creator_data)

                detail.update(top_creator_data)
                score_details.append(detail)

            top_creators = sorted(
                top_creators,
                key=top_creator_comparator,
                reverse=True,
            )
            # clean up extra keys
            for top_creator in top_creators:
                top_creator.pop("name")
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
            score_details.sort(reverse=True, key=top_creator_comparator)
            logger.info(f"summary of top 30: \n{pd.DataFrame(score_details[:30])}")

    def _get_score(self, movies, contest):
        score = {
            "score": 0,
            "recommend_count": 0,
        }
        avg_jury_rating = round(
            sum((movie.jury_rating or 0) for movie in movies) / len(movies), 2
        )
        avg_audience_rating = round(
            sum((movie.audience_rating or 0) for movie in movies) / len(movies), 2
        )

        no_audience_rating = min(
            sum(movie.reviews.count() for movie in movies) / len(movies),
            MAX_AUDIENCE_RATINGS,
        )

        non_celeb_recomms = sum(
            movie.in_lists.filter(
                contest=contest, owner__profile__is_celeb=False
            ).count()
            for movie in movies
        )
        celeb_recomms = sum(
            movie.in_lists.filter(
                contest=contest, owner__profile__is_celeb=True
            ).count()
            for movie in movies
        )
        avg_non_celeb_recomms = round(non_celeb_recomms / len(movies), 2)
        avg_celeb_recomms = round(celeb_recomms / len(movies), 2)

        # 20% avg jury
        jury_score = avg_jury_rating * 0.2
        # 10% avg audience
        audience_score = avg_audience_rating * 0.1
        # 10% avg audience rating count
        no_audience_score = no_audience_rating / MAX_AUDIENCE_RATINGS
        # 30% non celeb recommends
        non_celeb_recomms_score = min((avg_non_celeb_recomms * 0.025), 10) * 0.3
        # 30% celeb recommends
        celeb_recomms_score = min((avg_celeb_recomms * 2), 10) * 0.3
        logger.debug(
            f"celeb_recomms_score: {celeb_recomms_score} non_celeb_recomms_score:{non_celeb_recomms_score}"
        )

        scores = [
            jury_score,
            audience_score,
            no_audience_score,
            celeb_recomms_score,
            non_celeb_recomms_score,
        ]
        names = [
            "jury",
            "audience",
            "no. rating",
            "c recs",
            "nc recs",
        ]
        detail_score = dict(zip(names, scores))
        composite_score = (
            jury_score
            + audience_score
            + no_audience_score
            + celeb_recomms_score
            + non_celeb_recomms_score
        )
        logger.debug(f"composite_score {composite_score}")
        score["score"] = round(
            composite_score * 10,
            2,
        )
        score["recommend_count"] = non_celeb_recomms + celeb_recomms
        return score, detail_score

    def _get_movies_by_director(self, contest):
        movies_by_director = defaultdict(list)
        for movie in contest.movies.filter(state=MOVIE_STATE.PUBLISHED).all():
            directors = self._get_directors(movie)

            for director in directors:
                movies_by_director[director].append(movie)
        return movies_by_director

    def _get_directors(self, movie):
        return [
            dir_role.profile
            for dir_role in CrewMember.objects.filter(
                movie=movie, role__name="Director"
            ).all()
        ]
