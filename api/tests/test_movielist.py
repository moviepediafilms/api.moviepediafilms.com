from api.constants import RECOMMENDATION
from api.models import MovieList, User
from django.test import TestCase
from .base import reverse, APITestCaseMixin, LoggedInMixin


class MovieListTestCase(APITestCaseMixin, LoggedInMixin, TestCase):
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
        "movielist",
    ]

    def test_get_all_contest_recommend_movielist(self):
        url = reverse("api:movielist-list")
        res = self.client.get(url, {"contest__isnull": "false"})
        self.assertEqual(200, res.status_code)
        movie_list = res.json()["results"]
        self.assertEqual(1, len(movie_list))
        self.assertEqual(
            [
                {
                    "frozen": False,
                    "id": 1,
                    "like_count": 0,
                    "movies": [1],
                    "movies_count": 1,
                    "name": "January",
                    "owner": {
                        "email": "test@example.com",
                        "id": 1,
                        "image": None,
                        "name": "Test User",
                    },
                }
            ],
            movie_list,
        )

    def test_get_personal_recommend_movielist(self):
        url = reverse("api:movielist-list")
        res = self.client.get(url, {"name": "Recommendation", "owner_id": 1})
        self.assertEqual(200, res.status_code)
        movie_list = res.json()["results"]
        self.assertEqual(1, len(movie_list))
        self.assertEqual(
            [
                {
                    "frozen": False,
                    "id": 2,
                    "like_count": 0,
                    "movies": [],
                    "movies_count": 0,
                    "name": "Recommendation",
                    "owner": {
                        "email": "test@example.com",
                        "id": 1,
                        "image": None,
                        "name": "Test User",
                    },
                }
            ],
            movie_list,
        )

    def test_get_movies_of_movielist(self):
        url = reverse("api:movielist-movies", args=["v1", 1])
        res = self.client.get(url)
        self.assertEqual(200, res.status_code)
        actual_movies = res.json()["results"]
        self.assertEqual(
            [
                {
                    "id": 1,
                    "title": "Submitted Movie",
                    "poster": None,
                    "about": "",
                    "contests": [],
                    "crew": [],
                    "state": "P",
                    "score": 0.0,
                    "created_at": "2020-12-15T10:53:15.167332+05:30",
                    "recommend_count": 0,
                    "publish_on": None,
                    "runtime": 100.0,
                }
            ],
            actual_movies,
        )

    def test_like_movielist(self):
        movielist = MovieList.objects.get(name=RECOMMENDATION, owner_id=1)
        self.assertEqual(0, movielist.liked_by.count())
        url = reverse("api:movielist-like", args=["v1", 1])
        res = self.client.post(url)
        self.assertEqual(200, res.status_code)
        self.assertEqual({"success": True, "like_count": 1}, res.json())

    def test_unlike_movielist(self):
        movielist = MovieList.objects.get(name=RECOMMENDATION, owner_id=1)
        movielist.liked_by.add(User.objects.get(pk=1))
        self.assertEqual(1, movielist.liked_by.count())
        url = reverse("api:movielist-like", args=["v1", 1])
        res = self.client.delete(url)
        self.assertEqual(200, res.status_code)
        self.assertEqual({"success": True, "like_count": 0}, res.json())
