from logging import getLogger

from django.db import transaction
from django.core.management.base import BaseCommand
from api.models import Profile, MovieList


logger = getLogger(__name__)


# TODO: compare recommend list and celeb recommend and assign points accordingly
class Command(BaseCommand):
    def handle(self, *args, **options):
        with transaction.atomic():
            for profile in Profile.objects.filter(is_celeb=False).all():
                logger.info(f"{profile.user}: {profile.engagement_score}")
                engg_score = self._calculate_score(profile)
                profile.engagement_score = engg_score
                profile.save()
                logger.info(f"{profile.user}: {profile.engagement_score}")

            # updating curator ranks
            for index, profile in enumerate(
                Profile.objects.order_by("-engagement_score", "user__first_name").all()
            ):
                profile.curator_rank = index + 1
                profile.save()

    def _calculate_score(self, profile):
        review_points = self._get_review_points(profile)
        followers_points = self._get_followers_points(profile)
        curation_points = self._get_curation_points(profile)
        return round(review_points + followers_points + curation_points, 2)

    def _get_review_points(self, profile):
        """
        points for writing good content, each like on
        """
        reviews = profile.user.movieratereview_set.all()
        return sum(min(review.liked_by.count() * 0.25, 20) for review in reviews)

    def _get_followers_points(self, profile):
        """points for being followed by other users 0.25 per follower with no limit"""
        return profile.followed_by.count() * 0.25

    def _get_curation_points(self, profile):
        curation = MovieList.objects.filter(
            contest__isnull=False, owner=profile.user
        ).all()

        logger.debug(f"{len(curation)} curation from user in contests")
        return sum(min(c.liked_by.count() * 0.25, 200) for c in curation)
