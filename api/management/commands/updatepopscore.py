from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q, Count
from api.models import Role, CrewMember, Movie
from api.constants import MOVIE_STATE
from logging import getLogger

logger = getLogger(__name__)

PART_A_LEVELS = [
    512,
    1280,
    2560,
    3840,
    5120,
]
PART_B_LEVELS = [128, 320, 640, 960, 1280]


class Command(BaseCommand):
    def handle(self, *args, **options):
        with transaction.atomic():
            self.director_role = Role.objects.filter(name="Director").first()
            directors = self.director_role.profiles.all()
            logger.debug(f"updating {len(directors)} directors")
            for profile in directors:
                logger.info(f"{profile.user.username} => {profile.pop_score}")
                directed_movies = [
                    cm.movie
                    for cm in CrewMember.objects.filter(
                        role=self.director_role, profile=profile
                    )
                    if cm.movie.state == MOVIE_STATE.PUBLISHED
                ]
                logger.info(f"movies directed:  {len(directed_movies)}")
                followers_points = self.get_follower_points(profile)
                jury_points = self.get_jury_rating_points(directed_movies)
                recommend_points = self.get_recommend_points(directed_movies)
                rating_review_points = self.get_review_points(directed_movies)

                part_b = recommend_points + rating_review_points + jury_points
                part_a = followers_points

                capped_points = self._get_capped_points(part_a, part_b)

                profile.pop_score = capped_points
                logger.info(f"{profile.user.username} => {profile.pop_score}")
                profile.save()
            self.update_rank(directors)

    def _get_capped_points(self, part_a, part_b):
        level_a = self._get_part_a_level(part_a)
        level_b = self._get_part_b_level(part_b)
        level = min(level_a, level_b)
        logger.info(f"level: {level}")
        part_a = min(part_a, PART_A_LEVELS[level])
        part_b = min(part_b, PART_B_LEVELS[level])
        return part_a + part_b

    def _get_part_b_level(self, points):
        for level, limit in enumerate(PART_B_LEVELS):
            if points < limit:
                return level + 1
        return len(PART_B_LEVELS)

    def _get_part_a_level(self, num):
        for level, limit in enumerate(PART_A_LEVELS):
            if num < limit:
                return level + 1
        return len(PART_A_LEVELS)

    def update_rank(self, directors):
        directors = list(directors)
        directors.sort(
            key=lambda profile: (profile.pop_score, profile.user.get_full_name()),
            reverse=True,
        )
        for rank, profile in enumerate(directors):
            profile.creator_rank = rank + 1
            profile.save()

    def get_jury_rating_points(self, directed_movies):
        MULTIPLYER = 2.5
        jury_points = sum(m.jury_rating * MULTIPLYER for m in directed_movies)
        logger.debug(f"jury_points {jury_points}")
        return jury_points

    def get_follower_points(self, profile):
        """
        accountable for 20% of the points
        """
        MULTIPYER = 2
        logger.info(f"updating {profile.user.username}")
        followers_count = profile.followed_by.count()
        logger.info(f"followers_count {followers_count}")
        followers_points = followers_count * MULTIPYER
        logger.info(f"followers points {followers_points}")
        return followers_points

    def get_review_points(self, directed_movies):
        REVIEW_MULTIPYER = 1
        REVIEW_LIMIT = 20
        RATING_MULTIPYER = 0.5
        RATING_LIMIT = 50
        RATING_GTE = 7

        ratings_count = Count(
            "movieratereview", filter=Q(movieratereview__content__isnull=False)
        )
        reviews_count = Count(
            "movieratereview", filter=Q(movieratereview__rating__gte=RATING_GTE)
        )
        movies = (
            Movie.objects.filter(id__in=[m.id for m in directed_movies])
            .annotate(rating_count=ratings_count)
            .annotate(actual_review_count=reviews_count)
        )
        review_count = 0
        rating_count = 0
        for movie in movies:
            rating_count += min(RATING_LIMIT, movie.rating_count)
            review_count += min(REVIEW_LIMIT, movie.actual_review_count)
        logger.debug(f"rating: {rating_count}, review: {review_count}")
        return rating_count * RATING_MULTIPYER + review_count * REVIEW_MULTIPYER

    def get_recommend_points(self, directed_movies):
        MULTIPYER = 0.1
        RECOMMENT_LIMIT = 100
        recommended_count = 0
        for movie in directed_movies:
            recommended_count += min(
                movie.in_lists.exclude(contest_id__isnull=True).count(),
                RECOMMENT_LIMIT,
            )
        logger.debug(f"recommended {recommended_count} times")
        return recommended_count * MULTIPYER
