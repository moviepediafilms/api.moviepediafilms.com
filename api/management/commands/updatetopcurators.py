# Updates Top curators for live contests

from django.core.management.base import BaseCommand
from api.models import TopCurator, Contest
from logging import getLogger
from django.utils import timezone
from django.db import transaction
from itertools import chain

logger = getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        now = timezone.now()
        live_contests = Contest.objects.filter(start__lte=now, end__gte=now).all()
        logger.info(f"Live contests: {len(live_contests)}")
        curators = []
        for contest in live_contests:
            logger.info(f"Contest: {contest.name}")
            recommend_lists = (
                contest.movie_lists.all()
                .prefetch_related("owner__profile")
                .prefetch_related("movies")
            )
            celeb_recommend_lists = [
                rl for rl in recommend_lists if rl.owner.profile.is_celeb
            ]
            celeb_recommend_movies = list(
                chain(crl.movies for crl in celeb_recommend_lists)
            )
            logger.info(f"{len(celeb_recommend_movies)} movies recommended by celebs")
            audience_recommend_lists = [
                rl for rl in recommend_lists if not rl.owner.profile.is_celeb
            ]
            logger.info(f"{len(audience_recommend_lists)} people recommended movies")
            for recommend_list in audience_recommend_lists:
                curators.append(
                    TopCurator(
                        **{
                            "profile_id": recommend_list.owner.id,
                            "contest_id": contest.id,
                            "recommend_count": recommend_list.movies.count(),
                            "match": len(
                                set(recommend_list.movies.all()).intersection(
                                    celeb_recommend_movies
                                )
                            ),
                        }
                    )
                )

            with transaction.atomic():
                logger.info(f"deleting top curators")
                contest.top_curators.all().delete()
                logger.info(f"inserting {len(curators)} new curators")
                TopCurator.objects.bulk_create(curators, batch_size=100)
