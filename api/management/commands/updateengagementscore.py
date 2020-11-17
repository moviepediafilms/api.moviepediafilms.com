from logging import getLogger

from django.core.management.base import BaseCommand
from django.db.models import F
from api.models import Profile, MovieList
from collections import defaultdict
import itertools

logger = getLogger(__name__)


# TODO: compare recommend list and celeb recommend and assign points accordingly
class Command(BaseCommand):
    def handle(self, *args, **options):
        for profile in Profile.objects.all():
            logger.info(f"{profile.user}: {profile.engagement_score}")
            engg_score = self._calculate_score(profile)
            profile.engagement_score = engg_score
            profile.save()
            logger.info(f"{profile.user}: {profile.engagement_score}")

    def _calculate_score(self, profile):
        reviews = profile.user.movieratereview_set.all()
        review_points = self._get_review_points(reviews)
        jury_rating_similarity_points = self._get_jury_similarity_points(reviews)
        review_liked_points = self._get_review_liked_points(reviews)
        celeb_recommend_points = self._get_celeb_recommend_similarity_points(profile)
        return (
            review_points
            + jury_rating_similarity_points
            + review_liked_points
            + celeb_recommend_points
        )

    def _get_review_points(self, reviews):
        # since the reviews are fetched already, simple loop and filter in python instead of ORM query
        THRESHOLD = 140
        under_threshold = 0
        above_threshold = 0
        for review in reviews:
            if review.content:
                if len(review.content) < THRESHOLD:
                    under_threshold += 1
                else:
                    above_threshold += 1
        return under_threshold * 0.25 + above_threshold * 0.5

    def _get_jury_similarity_points(self, reviews):
        points = 0
        for review in reviews:
            if review.rating:
                points += 1.5 - 0.15 * abs(review.rating - review.movie.jury_rating)
        return points

    def _get_review_liked_points(self, reviews):
        points = 0
        MAX_PER_REVIEW = 35
        a = 1.75
        r = 0.05
        for review in reviews:
            if review.content:
                n = review.liked_by.count()
                points += min(a * (r ** n - 1) / r - 1, MAX_PER_REVIEW)
        return points

    def _get_celeb_recommend_similarity_points(self, profile):
        MULTIPLER = 20
        user_lists = MovieList.objects.filter(
            contest__isnull=False, owner=profile.user
        ).all()
        logger.debug(f"{len(user_lists)} users contest list in the system")
        contests = set([ul.contest for ul in user_lists])
        logger.debug(f"contests {contests}")
        celebs = [p.user for p in Profile.objects.filter(is_celeb=True).all()]
        logger.debug(f"celeb user id {celebs}")
        logger.debug(f"{len(celebs)} celebs in the system")
        celeb_recomm_lists = MovieList.objects.filter(
            contest_id__in=contests, owner_id__in=celebs
        ).all()
        logger.debug(f"Celeb recommends lists {celeb_recomm_lists}")
        logger.debug(f"user recommends lists {user_lists}")
        contest_lists = defaultdict(list)
        for recomm_list in itertools.chain(celeb_recomm_lists, user_lists):
            contest_lists[recomm_list.contest].append(recomm_list)

        points = 0
        for contest, lists in contest_lists.items():
            if len(lists) == 2:
                celeb_list, user_list = lists
                contest_points = len(
                    set([m.id for m in celeb_list.movies.all()]).intersection(
                        set([m.id for m in user_list.movies.all()])
                    )
                )
                logger.debug(f"for contest {contest.name}: {contest_points}")
                points += contest_points
        logger.debug(f"total celeb recommend points {points}")
        return points * MULTIPLER
