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
        for contest in live_contests:
            curators = []
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
                chain(*[crl.movies.all() for crl in celeb_recommend_lists])
            )
            logger.info(f"{len(celeb_recommend_movies)} movies recommended by celebs")
            audience_recommend_lists = [
                rl for rl in recommend_lists if not rl.owner.profile.is_celeb
            ]
            logger.info(f"{len(audience_recommend_lists)} people recommended movies")
            for recommend_list in audience_recommend_lists:
                likes = recommend_list.liked_by.count()
                recommended_movies = recommend_list.movies.all()

                # Recommendation Weight: No. of recommendations made/Max. Reco
                recommend_wt = 0
                if contest.max_recommends:
                    recommend_wt = len(recommended_movies) / contest.max_recommends

                match_count = len(
                    set(recommended_movies).intersection(celeb_recommend_movies)
                )
                # Match accuracy: No. of matched recommendations/No. of recommendations made
                match_accuracy = 0
                if recommended_movies:
                    match_accuracy = match_count / len(recommended_movies)

                # Celebrity Match accuracy: No. of matched reco./Total films on celebrity List
                match_accuracy_with_celeb = 0
                if celeb_recommend_movies:
                    match_accuracy_with_celeb = match_count / len(
                        celeb_recommend_movies
                    )

                likes_for_calc = likes / 10**6

                # Composite Score (A): Reco. Wt. * Match Accuracy * Match accuracy with celeb
                score = (
                    likes_for_calc
                    + recommend_wt * match_accuracy * match_accuracy_with_celeb
                )
                score = round(score, 6)

                match_percent_for_ui = int(match_accuracy_with_celeb * 100)
                curators.append(
                    {
                        "profile_id": recommend_list.owner.profile.id,
                        "contest_id": contest.id,
                        "likes_on_recommend": likes,
                        "match": match_percent_for_ui,
                        "score": score,
                    }
                )

            curators = sorted(curators, key=lambda x: x.get("score"), reverse=True)
            curators = [
                TopCurator(pos=pos + 1, **data) for pos, data in enumerate(curators)
            ]
            with transaction.atomic():
                logger.info("deleting top curators")
                contest.top_curators.all().delete()

                logger.info(f"inserting {len(curators)} new curators")
                TopCurator.objects.bulk_create(curators, batch_size=100)
