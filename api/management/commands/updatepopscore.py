from django.core.management.base import BaseCommand
from django.db.models import Q, Count
from api.models import Role, CrewMember, Movie
from api.constants import MOVIE_STATE
from logging import getLogger

logger = getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
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

            profile.pop_score = (
                followers_points + recommend_points + rating_review_points + jury_points
            )
            logger.info(f"{profile.user.username} => {profile.pop_score}")
            profile.save()
        self.update_rank(directors)

    def update_rank(self, directors):
        directors = list(directors)
        directors.sort(key=lambda profile: profile.pop_score)
        for rank, profile in enumerate(directors):
            profile.rank = rank + 1
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
            .annotate(review_count=reviews_count)
        )
        review_count = 0
        rating_count = 0
        for movie in movies:
            rating_count += min(RATING_LIMIT, movie.rating_count)
            review_count += min(REVIEW_LIMIT, movie.review_count)
        logger.debug(f"rating: {rating_count}, review: {review_count}")
        return rating_count * RATING_MULTIPYER + review_count * REVIEW_MULTIPYER

    def get_recommend_points(self, directed_movies):
        MULTIPYER = 0.1
        RECOMMENT_LIMIT = 100
        recommended_count = 0
        for movie in directed_movies:
            recommended_count += min(
                movie.in_lists.filter(name="Recommendation").count(), RECOMMENT_LIMIT
            )
        logger.debug(f"recommended {recommended_count} times")
        return recommended_count * MULTIPYER
