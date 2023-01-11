from api.constants import MOVIE_STATE, RECOMMENDATION
from api.models import MovieList, Movie, User, Profile
from django.test import TestCase
from .base import reverse, APITestCaseMixin, LoggedInMixin


class PersonalRecommendListTestCase(APITestCaseMixin, LoggedInMixin, TestCase):
    fixtures = ["user", "profile", "genre", "lang", "role", "movie", "package", "order"]

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
                    "poster_thumb": None,
                    "about": "This is a good movie",
                    "contests": [],
                    "crew": [],
                    "state": "P",
                    "score": 0.0,
                    "created_at": "2020-12-15T10:53:15.167332+05:30",
                    "recommend_count": 0,
                    "publish_on": "2021-01-01T10:53:15.167332+05:30",
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


class CelebTestCase(APITestCaseMixin, TestCase):
    fixtures = ["user", "profile", "role"]

    def setUp(self):
        super().setUp()
        profile = Profile.objects.get(pk=1)
        profile.is_celeb = True
        profile.celeb_order = 2
        profile.save()
        self._create_celeb()

    def _create_celeb(self):
        user = User.objects.create(username="celeb1", email="celeb1@example.com")
        Profile.objects.create(user=user, is_celeb=True, celeb_order=1)

    def test_get_celebs(self):
        url = reverse("api:profile-list", args=["v1"])
        res = self.client.get(url, dict(is_celeb=True))
        self.assertEqual(200, res.status_code)
        expected_profiles = [
            {
                "profile_id": 1,
                "about": None,
                "title": None,
                "city": None,
                "gender": None,
                "roles": [],
                "image": "/default_avatar_m.png",
                "is_celeb": True,
                "level": 1,
                "creator_rank": -1,
                "curator_rank": -1,
                "engagement_score": 0.0,
                "mcoins": 0.0,
                "pop_score": 0.0,
                "follows": [],
                "movies_directed": 0,
                "id": 1,
                "name": "Test User",
            },
            {
                "profile_id": 2,
                "about": None,
                "title": None,
                "city": None,
                "gender": None,
                "roles": [],
                "image": "/default_avatar_m.png",
                "is_celeb": True,
                "level": 1,
                "creator_rank": -1,
                "curator_rank": -1,
                "engagement_score": 0.0,
                "mcoins": 0.0,
                "pop_score": 0.0,
                "follows": [],
                "movies_directed": 0,
                "id": 2,
                "name": "",
            },
        ]
        self.assertEqual(expected_profiles, res.json()["results"])
