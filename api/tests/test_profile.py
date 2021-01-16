from api.constants import MOVIE_STATE, RECOMMENDATION
from api.models import MovieList, Movie, User
from django.test import TestCase
from .base import reverse, APITestCaseMixin, LoggedInMixin


class PersonalRecommendListTestCase(APITestCaseMixin, LoggedInMixin, TestCase):
    fixtures = ["user", "profile", "genre", "lang", "role", "order", "movie"]

    def _recommend_movie(self):
        owner = User.objects.get(pk=1)
        movie = Movie.objects.get(pk=1)
        movie_list = MovieList.objects.create(name=RECOMMENDATION, owner=owner)
        movie_list.movies.add(movie)

    def test_get_user_recommend_movies(self):
        self._recommend_movie()
        url = reverse("api:profile-recommends", args=["v1", 1])
        res = self.client.get(url)
        self.assertEquals(200, res.status_code)
        actual_movies = res.json()["results"]
        self.assertEqual(1, len(actual_movies))
        self.assertEquals(
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

    def test_recommend_movie(self):
        url = reverse("api:profile-recommends", args=["v1", 1])
        res = self.client.post(url, dict(movie=1))
        self.assertEqual(200, res.status_code)
        self.assertEqual([{"id": 1}], res.json()["recommended"])

    def test_undo_recommended_movie(self):
        self._recommend_movie()
        recommend_list = MovieList.objects.get(name=RECOMMENDATION, owner_id=1)
        self.assertEqual(1, recommend_list.movies.count())
        url = reverse("api:profile-recommends", args=["v1", 1])
        res = self.client.delete(url, dict(movie=1))
        self.assertEqual(200, res.status_code)
        self.assertEqual([], res.json()["recommended"])

    def test_recommend_unpublished_movie(self):
        movie = Movie.objects.get(pk=1)
        movie.state = MOVIE_STATE.CREATED
        movie.save()

        url = reverse("api:profile-recommends", args=["v1", 1])
        res = self.client.post(url, dict(movie=1))
        self.assertEqual(400, res.status_code)
        self.assertEqual({"movie": ["Movie does not exist"]}, res.json())
