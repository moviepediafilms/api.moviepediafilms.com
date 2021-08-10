from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from api.models.contest import ContestType
from api.constants import CONTEST_STATE, MOVIE_STATE
from api.models import Release, Movie, Contest


class ReleaseTestCase(TestCase):
    maxDiff = None
    fixtures = [
        "user",
        "profile",
        "genre",
        "lang",
        "role",
        "package",
        "order",
        "movie",
        "contest_type",
        "contest",
        "crewmember",
    ]

    def setUp(self):
        super().setUp()
        self.movie = Movie.objects.get(pk=1)
        self.movie.state = MOVIE_STATE.CREATED
        self.movie.save()

        self.contest = Contest.objects.get(pk=1)

    def test_realese_updates_movie(self):
        self.assertNotEqual(self.movie.state, MOVIE_STATE.PUBLISHED)

        release = Release.objects.create(movie=self.movie, contest=self.contest)

        self.assertIn(self.contest, self.movie.contests.all())
        self.assertEqual(self.movie.publish_on, release.on)
        self.assertEqual(self.movie.state, MOVIE_STATE.PUBLISHED)

    def test_multiple_releases(self):
        self.assertNotEqual(self.movie.state, MOVIE_STATE.PUBLISHED)

        contest1 = self.contest
        Release.objects.create(movie=self.movie, contest=contest1)

        monthly_contest_type = ContestType.objects.get(pk=1)
        contest2 = Contest.objects.create(
            name="contest2",
            start=timezone.now(),
            end=timezone.now() + timedelta(days=20),
            type=monthly_contest_type,
            state=CONTEST_STATE.LIVE,
        )
        release2 = Release.objects.create(movie=self.movie, contest=contest2)

        self.assertIn(contest1, self.movie.contests.all())
        self.assertIn(contest2, self.movie.contests.all())
        self.assertEqual(self.movie.publish_on, release2.on)
        self.assertEqual(self.movie.state, MOVIE_STATE.PUBLISHED)
