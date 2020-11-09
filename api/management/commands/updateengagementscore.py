from django.core.management.base import BaseCommand
from api.models import Profile
from logging import getLogger

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
        return review_points + jury_rating_similarity_points + review_liked_points

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
