from api.models.movie import MpGenre
import math
from unittest import mock
from datetime import datetime

from django.utils import timezone
from django.test import TestCase

from .base import reverse, APITestCaseMixin, LoggedInMixin


class NewReleasesTestCase(APITestCaseMixin, LoggedInMixin, TestCase):
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
        "new_releases",
    ]

    def test_new_releases(self):
        res = self.client.get(reverse("api:movie-new-releases"))
        self.assertEqual(200, res.status_code)
        actual_movies = res.json()["results"]
        self.assertEquals(2, len(actual_movies))
        # assert that all the publish dates are same
        publish_dates = set(
            datetime.strptime(movie["publish_on"], "%Y-%m-%dT%H:%M:%S.%f%z").date()
            for movie in actual_movies
        )
        self.assertEqual(1, len(publish_dates))


class MostRecommendedTestCase(APITestCaseMixin, LoggedInMixin, TestCase):
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
        "test_most_recommended",
    ]

    def test_most_recommended(self):
        res = self.client.get(
            reverse("api:movie-list"), {"ordering": "-recommend_count"}
        )
        self.assertEqual(200, res.status_code)
        actual_movies = res.json()["results"]
        self.assertEquals(4, len(actual_movies))
        last_recommend_count = math.inf
        for movie in actual_movies:
            recommend_count = movie.get("recommend_count")
            self.assertIsNotNone(recommend_count)
            self.assertLessEqual(
                recommend_count,
                last_recommend_count,
                [m.get("recommend_count") for m in actual_movies],
            )
            last_recommend_count = recommend_count


@mock.patch("api.views.contest.timezone")
class LiveContestTestCase(APITestCaseMixin, LoggedInMixin, TestCase):
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
        "test_live_contest_categories",
    ]
    feb_3_2020 = timezone.now().replace(year=2021, month=2, day=3)

    def test_live_contests(self, mocked_timezone):
        mocked_timezone.now.return_value = self.feb_3_2020
        res = self.client.get(reverse("api:contest-list"), {"live": "true"})
        self.assertEqual(200, res.status_code)
        live_contest = res.json()["results"]
        self.assertEqual(2, len(live_contest))
        # check current date is between start and end

        parse_datetime = lambda s: datetime.strptime(  # noqa: E731
            s, "%Y-%m-%dT%H:%M:%S%z"
        )
        for contest in live_contest:
            self.assertGreaterEqual(self.feb_3_2020, parse_datetime(contest["start"]))
            self.assertLessEqual(self.feb_3_2020, parse_datetime(contest["end"]))

    def test_movies_in_contest(self, mocked_timezone):
        mocked_timezone.now.return_value = self.feb_3_2020
        res = self.client.get(reverse("api:contest-movies", args=["v1", 1]))
        self.assertEqual(200, res.status_code)
        actual_movies = res.json()["results"]
        self.assertEqual(3, len(actual_movies))
        self.assertEqual(
            [
                {
                    "id": 4,
                    "title": "Movie4",
                    "poster": None,
                    "poster_thumb": None,
                    "about": "This is a good movie4",
                    "contests": ["January"],
                    "crew": [],
                    "state": "P",
                    "score": 0.0,
                    "created_at": "2020-12-15T10:53:15.167332+05:30",
                    "recommend_count": 3,
                    "publish_on": "2021-01-10T10:53:15.167332+05:30",
                    "runtime": 100.0,
                },
                {
                    "id": 3,
                    "title": "Movie3",
                    "poster": None,
                    "poster_thumb": None,
                    "about": "This is a good movie3",
                    "contests": ["January"],
                    "crew": [],
                    "state": "P",
                    "score": 0.0,
                    "created_at": "2020-12-15T10:53:15.167332+05:30",
                    "recommend_count": 2,
                    "publish_on": "2021-01-10T08:53:15.167332+05:30",
                    "runtime": 100.0,
                },
                {
                    "id": 2,
                    "title": "Movie2",
                    "poster": None,
                    "poster_thumb": None,
                    "about": "This is a good movie2",
                    "contests": ["January"],
                    "crew": [],
                    "state": "P",
                    "score": 0.0,
                    "created_at": "2020-12-15T10:53:15.167332+05:30",
                    "recommend_count": 1,
                    "publish_on": "2021-01-01T10:53:15.167332+05:30",
                    "runtime": 100.0,
                },
            ],
            actual_movies,
        )


class MpGenreMoviesTestCase(APITestCaseMixin, LoggedInMixin, TestCase):
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
        "test_mp_live_genre",
    ]

    def test_movies_in_live_mp_genre(self):
        res = self.client.get(reverse("api:mpgenre-movies", args=["v1", 1]))
        self.assertEqual(200, res.status_code)
        actual_movies = res.json()["results"]
        self.assertEqual(2, len(actual_movies))
        self.assertEqual(3, MpGenre.objects.count())
        self.assertEqual(
            [
                {
                    "id": 2,
                    "title": "Submitted Movie2",
                    "poster": None,
                    "poster_thumb": None,
                    "about": "This is a good movie2",
                    "contests": [],
                    "crew": [],
                    "state": "P",
                    "score": 0.0,
                    "created_at": "2020-12-15T10:53:15.167332+05:30",
                    "recommend_count": 0,
                    "publish_on": "2021-01-01T10:53:15.167332+05:30",
                    "runtime": 100.0,
                },
                {
                    "id": 4,
                    "title": "Submitted Movie3",
                    "poster": None,
                    "poster_thumb": None,
                    "about": "This is a good movie4",
                    "contests": [],
                    "crew": [],
                    "state": "P",
                    "score": 0.0,
                    "created_at": "2020-12-15T10:53:15.167332+05:30",
                    "recommend_count": 0,
                    "publish_on": "2021-01-01T10:53:15.167332+05:30",
                    "runtime": 100.0,
                },
            ],
            actual_movies,
        )

    def test_get_live_genres(self):
        res = self.client.get(reverse("api:mpgenre-list"))
        self.assertEqual(200, res.status_code)
        actual_mp_genre = res.json()["results"]
        self.assertEqual(2, len(actual_mp_genre))
        for mp_genre in actual_mp_genre:
            self.assertTrue(mp_genre["live"])
