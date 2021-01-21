from api.constants import CONTEST_STATE
from api.models import MovieList, Contest, Movie
from django.test import TestCase
from .base import reverse, APITestCaseMixin, LoggedInMixin


class ContestTestCase(APITestCaseMixin, LoggedInMixin, TestCase):
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
    ]

    def _add_movie_in_contest(self):
        contest = Contest.objects.get(pk=1)
        movie = Movie.objects.get(pk=1)
        contest.movies.add(movie)

    def _create_movie_list_for_contest(self):
        contest = Contest.objects.get(pk=1)
        return MovieList.objects.create(contest=contest, name=contest.name, owner_id=1)

    def test_recommend_non_participating_movie_in_live_contest(self):
        url = reverse("api:contest-recommend", args=["v1", 1])
        res = self.client.post(url, {"movie": 1})
        self.assertEqual(400, res.status_code)
        self.assertEqual(
            {"non_field_errors": ["Film hasn't participated in this contest"]},
            res.json(),
        )

    def test_recommend_movie_non_live_contest(self):
        contest = Contest.objects.get(pk=1)
        contest.state = CONTEST_STATE.FINISHED
        contest.save()
        url = reverse("api:contest-recommend", args=["v1", 1])
        res = self.client.post(url, {"movie": 1})
        self.assertEqual(400, res.status_code)
        self.assertEqual(
            {"non_field_errors": ["Contest is not live"]},
            res.json(),
        )

    def test_recommend_movie_in_live_contest(self):
        self._add_movie_in_contest()
        movie_list = self._create_movie_list_for_contest()
        self.assertEqual(0, movie_list.movies.count())

        url = reverse("api:contest-recommend", args=["v1", 1])
        res = self.client.post(url, {"movie": 1})
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, res.json()["recommended"])

    def test_undo_recommend_movie_in_live_contest(self):
        self._add_movie_in_contest()
        movie_list = self._create_movie_list_for_contest()
        movie_list.movies.add(Movie.objects.get(pk=1))
        url = reverse("api:contest-recommend", args=["v1", 1])
        res = self.client.get(url)
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, res.json()["recommended"])

        res = self.client.delete(url, {"movie": 1})
        self.assertEqual(200, res.status_code)
        self.assertEqual(0, res.json()["recommended"])

    def test_get_recommend_movie_in_live_contest(self):
        url = reverse("api:contest-recommend", args=["v1", 1])
        res = self.client.get(url)
        self.assertEqual(200, res.status_code)
        self.assertEqual(0, res.json()["recommended"])

        contest = Contest.objects.get(pk=1)
        movie_list = MovieList.objects.create(
            contest=contest, owner_id=1, name=contest.name
        )
        movie_list.movies.add(Movie.objects.get(pk=1))

        res = self.client.get(url)
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, res.json()["recommended"])

    def test_get_live_contests(self):
        res = self.client.get(reverse("api:contest-list"), {"live": "true"})
        self.assertEqual(200, res.status_code)
        actual_contests = res.json()["results"]
        self.assertEqual(1, len(actual_contests))
        self.assertEqual(
            [
                {
                    "id": 1,
                    "name": "January",
                    "is_live": True,
                    "start": "2021-01-01T00:14:10+05:30",
                    "end": "2021-02-16T00:14:15+05:30",
                    "recommended_movies": [],
                }
            ],
            actual_contests,
        )


class AnonUserContestTestCase(APITestCaseMixin, TestCase):
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
    ]

    def test_get_live_contests(self):
        res = self.client.get(reverse("api:contest-list"), {"live": "true"})
        self.assertEqual(200, res.status_code)
        actual_contests = res.json()["results"]
        self.assertEqual(1, len(actual_contests))
        self.assertEqual(
            [
                {
                    "id": 1,
                    "name": "January",
                    "is_live": True,
                    "start": "2021-01-01T00:14:10+05:30",
                    "end": "2021-02-16T00:14:15+05:30",
                    "recommended_movies": [],
                }
            ],
            actual_contests,
        )
