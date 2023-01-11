from django.test import TestCase
from .base import reverse, APITestCaseMixin, LoggedInMixin


class MovieViewTestCase(APITestCaseMixin, LoggedInMixin, TestCase):
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

    def test_get_movie_details(self):
        url = reverse("api:movie-detail", args=["v1", 1])
        res = self.client.get(url)
        self.assertEqual(200, res.status_code)
        self.assertEqual(
            {
                "id": 1,
                "order": {
                    "id": 1,
                    "owner": 1,
                    "order_id": None,
                    "amount": None,
                    "package": 1,
                    "payment_id": None,
                    "state": "C",
                },
                "title": "Submitted Movie",
                "link": "http://facebook.com",
                "state": "P",
                "runtime": 100.0,
                "genres": [{"id": 1, "name": "Drama"}],
                "lang": {"id": 1, "name": "English"},
                "poster": None,
                "poster_thumb": None,
                "package": {"amount": 100.0, "name": "Pack1"},
                "crew": [
                    {
                        "profile": {
                            "city": None,
                            "creator_rank": -1,
                            "curator_rank": -1,
                            "engagement_score": 0.0,
                            "pop_score": 0.0,
                            "id": 1,
                            "is_celeb": False,
                            "image": "/default_avatar_m.png",
                            "level": 1,
                            "name": "Test User",
                            "profile_id": 1,
                        },
                        "roles": [{"name": "Director"}],
                    }
                ],
                "jury_rating": 0.0,
                "audience_rating": 0.0,
                "requestor_rating": {"content": "", "rating": None, "rated_at": None},
                "is_watchlisted": False,
                "is_recommended": False,
                "publish_on": "2021-01-01T10:53:15.167332+05:30",
                "about": "This is a good movie",
                "approved": True,
                "recommend_count": 0,
                "contests": [],
                "type": "S",
            },
            res.json(),
        )

    def test_get_movies(self):
        res = self.client.get(reverse("api:movie-list"))
        self.assertEqual(200, res.status_code)
        actual_movies = res.json()["results"]
        self.assertEqual(1, len(actual_movies))
        self.assertEqual(
            [
                {
                    "about": "This is a good movie",
                    "contests": [],
                    "created_at": "2020-12-15T10:53:15.167332+05:30",
                    "crew": [
                        {"name": "Test User", "profile_id": 1, "role": "Director"}
                    ],
                    "id": 1,
                    "poster": None,
                    "poster_thumb": None,
                    "publish_on": "2021-01-01T10:53:15.167332+05:30",
                    "recommend_count": 0,
                    "runtime": 100.0,
                    "score": 0.0,
                    "state": "P",
                    "title": "Submitted Movie",
                }
            ],
            actual_movies,
        )

    def test_movies_by(self):
        """test movies by a director"""
        res = self.client.get(reverse("api:moviesby-detail", args=["v1", 2]))
        self.assertEqual(404, res.status_code)

        res = self.client.get(reverse("api:moviesby-detail", args=["v1", 1]))
        self.assertEqual(200, res.status_code)
        actual_movies = res.json()["results"]
        self.assertEqual(
            [
                {
                    "id": 1,
                    "title": "Submitted Movie",
                    "poster": None,
                    "poster_thumb": None,
                    "about": "This is a good movie",
                    "contests": [],
                    "crew": [
                        {"role": "Director", "profile_id": 1, "name": "Test User"}
                    ],
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
