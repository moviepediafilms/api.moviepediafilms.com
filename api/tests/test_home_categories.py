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
        "most_recommended",
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
        "live_contest_categories",
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
        res = self.client.get(reverse("api:contest-list"), {"live": "true"})
        self.assertEqual(200, res.status_code)


class MpGenreTestCase(APITestCaseMixin, LoggedInMixin, TestCase):
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
        "mp_live_genre",
    ]

    def test_get_live_mp_genres(self):
        self.fail()