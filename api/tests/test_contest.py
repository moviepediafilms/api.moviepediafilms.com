from django.utils import timezone
from django.test import TestCase
from django.core.management import call_command

from api.constants import CONTEST_STATE
from api.models import MovieList, Contest, Movie, User, Profile, CrewMember, Role
from .base import reverse, APITestCaseMixin, LoggedInMixin


def _add_movie_in_contest(movie_id=1, pk=1):
    contest = Contest.objects.get(pk=pk)
    movie = Movie.objects.get(pk=movie_id)
    contest.movies.add(movie)


def _make_contest_end_tomm(pk=1):
    contest = Contest.objects.get(pk=pk)
    contest.end = timezone.localtime(timezone.now() + timezone.timedelta(days=1))
    contest.microsecond = 0
    contest.save()
    return contest.end.isoformat()


def _create_movie_list_for_contest(pk=1, owner_id=1):
    contest = Contest.objects.get(pk=pk)
    return MovieList.objects.create(
        contest=contest, name=contest.name, owner_id=owner_id
    )


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
        "crewmember",
        "contest_type",
        "contest",
    ]

    def setUp(self):
        movie = Movie.objects.get(pk=1)
        movie.publish_on = timezone.now() - timezone.timedelta(days=5)
        movie.save()

        self.end = _make_contest_end_tomm()
        return super().setUp()

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
        _add_movie_in_contest()
        movie_list = _create_movie_list_for_contest()
        self.assertEqual(0, movie_list.movies.count())

        url = reverse("api:contest-recommend", args=["v1", 1])
        res = self.client.post(url, {"movie": 1})
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, res.json()["recommended"])

    def test_undo_recommend_movie_in_live_contest(self):
        _add_movie_in_contest()
        movie_list = _create_movie_list_for_contest()
        movie_list.movies.add(Movie.objects.get(pk=1))
        url = reverse("api:contest-recommend", args=["v1", 1])
        res = self.client.get(url)
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, res.json()["recommended"])

        res = self.client.delete(url, {"movie": 1})
        self.assertEqual(200, res.status_code)
        self.assertEqual(0, res.json()["recommended"])

    def test_recommend_more_than_allowed(self):
        # reduce the maximum allowed recommendation for this contest
        contest = Contest.objects.get(pk=1)
        contest.max_recommends = 1
        contest.save()
        # we need at least 2 movies to perform the test
        new_movie = Movie.objects.get(pk=1)
        new_movie.pk = None
        new_movie.link = "http://dummy_movie2.com"
        new_movie.save()
        # add movies to contest
        _add_movie_in_contest(movie_id=1)
        _add_movie_in_contest(movie_id=2)
        # create a movielist of logged in user
        movie_list = _create_movie_list_for_contest()

        self.assertEqual(0, movie_list.movies.count())
        self.assertEqual(1, contest.max_recommends)

        # allow the first recommend
        url = reverse("api:contest-recommend", args=["v1", 1])
        res = self.client.post(url, {"movie": 1})
        self.assertEqual(200, res.status_code)

        self.assertEqual(1, res.json()["recommended"])
        # block the next recommend
        url = reverse("api:contest-recommend", args=["v1", 1])
        res = self.client.post(url, {"movie": 1})
        self.assertEqual(400, res.status_code)
        self.assertEqual(
            {
                "non_field_errors": [
                    "You ran out of recommends (1/1) for January. Undo the recommends from your profile to continue."
                ]
            },
            res.json(),
        )
        # but allow undo recommendation
        res = self.client.delete(url, {"movie": 1})
        self.assertEqual(200, res.status_code)
        self.assertEqual(
            {"id": 1, "name": "January", "recommended": 0, "max_recommends": 1},
            res.json(),
        )

    def test_recommend_after_contest_live_days_per_movie_is_over(self):
        # reduce the maximum allowed recommendation for this contest
        contest = Contest.objects.get(pk=1)
        contest.days_per_movie = 2
        contest.save()

        movie = Movie.objects.get(pk=1)
        movie.publish_on = timezone.now() - timezone.timedelta(days=5)
        movie.save()

        _add_movie_in_contest()

        url = reverse("api:contest-recommend", args=["v1", 1])
        res = self.client.post(url, {"movie": 1})
        self.assertEqual(400, res.status_code)
        self.assertEqual(
            {
                "movie": [
                    "Recommendation Period of this film for January is now closed. Try other films."
                ]
            },
            res.json(),
        )

    def test_undo_recommend_after_contest_live_days_per_movie_is_over(self):
        # reduce the maximum allowed recommendation for this contest
        contest = Contest.objects.get(pk=1)
        contest.days_per_movie = 2
        contest.save()

        movie = Movie.objects.get(pk=1)
        movie.publish_on = timezone.now() - timezone.timedelta(days=5)
        movie.save()

        _add_movie_in_contest()

        url = reverse("api:contest-recommend", args=["v1", 1])
        res = self.client.delete(url, {"movie": 1})
        self.assertEqual(200, res.status_code)
        self.assertEqual(
            {"id": 1, "name": "January", "recommended": 0, "max_recommends": 20},
            res.json(),
        )

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
                    "end": self.end,
                    "recommended_movies": [],
                }
            ],
            actual_contests,
        )

    def test_my_creator_position_not_participated(self):
        res = self.client.get(
            reverse("api:contest-my-creator-position", args=["v1", 1])
        )
        self.assertEqual(res.status_code, 404)

    def test_my_creator_position(self):
        _add_movie_in_contest()
        call_command("updatetopcreators")
        res = self.client.get(
            reverse("api:contest-my-creator-position", args=["v1", 1])
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(),
            {
                "score": 0.0,
                "recommend_count": 0,
                "profile_id": 1,
                "image": "/default_avatar_m.png",
                "creator_rank": -1,
                "curator_rank": -1,
                "level": 1,
                "is_celeb": False,
                "engagement_score": 0.0,
                "pop_score": 0.0,
                "city": None,
                "id": 1,
                "name": "Test User",
                "pos": 1,
            },
        )

    def test_my_curator_position_not_participated(self):
        res = self.client.get(
            reverse("api:contest-my-curator-position", args=["v1", 1])
        )
        self.assertEqual(res.status_code, 404)

    def test_my_curator_position(self):
        _add_movie_in_contest()
        movie_list = _create_movie_list_for_contest()
        movie_list.movies.add(Movie.objects.get(pk=1))

        call_command("updatetopcurators")
        res = self.client.get(
            reverse("api:contest-my-curator-position", args=["v1", 1])
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(),
            {
                "match": 0.0,
                "likes_on_recommend": 0,
                "score": 0.0,
                "profile_id": 1,
                "image": "/default_avatar_m.png",
                "creator_rank": -1,
                "curator_rank": -1,
                "level": 1,
                "is_celeb": False,
                "engagement_score": 0.0,
                "pop_score": 0.0,
                "city": None,
                "id": 1,
                "pos": 1,
                "name": "Test User",
            },
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
        "crewmember",
        "contest_type",
        "contest",
    ]

    def setUp(self):
        super().setUp()
        self.end = _make_contest_end_tomm()

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
                    "end": self.end,
                    "recommended_movies": [],
                }
            ],
            actual_contests,
        )

    def test_get_top_creators(self):
        _add_movie_in_contest()

        movie_list = _create_movie_list_for_contest()
        movie = Movie.objects.get(pk=1)
        movie.jury_rating = 5
        movie.audience_rating = 8
        movie.save()

        movie_list.movies.add(movie)

        call_command("updatetopcreators")
        res = self.client.get(reverse("api:contest-top-creators", args=["v1", 1]))
        self.assertEqual(200, res.status_code)
        actual_top_creators = res.json()["results"]
        self.assertEquals(
            [
                {
                    "score": 18.08,
                    "recommend_count": 1,
                    "profile_id": 1,
                    "image": "/default_avatar_m.png",
                    "creator_rank": -1,
                    "curator_rank": -1,
                    "level": 1,
                    "is_celeb": False,
                    "engagement_score": 0.0,
                    "pop_score": 0.0,
                    "city": None,
                    "id": 1,
                    "pos": 1,
                    "name": "Test User",
                }
            ],
            actual_top_creators,
        )

    def test_get_top_creators_multiple_movies(self):
        # duplicate movie
        movie_dupe = Movie.objects.get(pk=1)
        movie_dupe.link += ".sample.com"
        movie_dupe.id = None
        movie_dupe.jury_rating = 9
        movie_dupe.audience_rating = 9
        movie_dupe.save()
        CrewMember.objects.create(
            profile=Profile.objects.get(pk=1),
            movie=movie_dupe,
            role=Role.objects.get(name="Director"),
        )
        _add_movie_in_contest(movie_id=1)
        _add_movie_in_contest(movie_id=2)
        self.assertTrue(Contest.objects.get(pk=1).movies.count(), 2)

        movie_list = _create_movie_list_for_contest()
        movie = Movie.objects.get(pk=1)
        movie.jury_rating = 5
        movie.audience_rating = 8
        movie.save()

        movie_list.movies.add(movie)
        movie_list.movies.add(movie_dupe)

        call_command("updatetopcreators")
        res = self.client.get(reverse("api:contest-top-creators", args=["v1", 1]))
        self.assertEqual(200, res.status_code)
        actual_top_creators = res.json()["results"]
        self.assertEquals(
            [
                {
                    "score": 22.57,
                    "recommend_count": 2,
                    "profile_id": 1,
                    "image": "/default_avatar_m.png",
                    "creator_rank": -1,
                    "curator_rank": -1,
                    "level": 1,
                    "is_celeb": False,
                    "engagement_score": 0.0,
                    "pop_score": 0.0,
                    "city": None,
                    "id": 1,
                    "pos": 1,
                    "name": "Test User",
                }
            ],
            actual_top_creators,
        )

    def test_my_creator_position(self):
        res = self.client.get(
            reverse("api:contest-my-creator-position", args=["v1", 1])
        )
        self.assertEquals(res.status_code, 401)

    def test_my_curator_position(self):
        res = self.client.get(
            reverse("api:contest-my-curator-position", args=["v1", 1])
        )
        self.assertEquals(res.status_code, 401)


class TestTopCurator(APITestCaseMixin, TestCase):
    fixtures = [
        "test_top_curators",
        "genre",
        "lang",
        "role",
        "package",
        "order",
        "movie",
        "contest_type",
        "contest",
    ]

    def setUp(self):
        super().setUp()
        self.end = _make_contest_end_tomm()

    def test_get_top_curators(self):
        _add_movie_in_contest()

        # create a celeb profile
        celeb_user = User.objects.create(username="A Celeb", email="celeb@example.com")
        Profile.objects.create(user=celeb_user, is_celeb=True)

        # build celeb recommends list
        celeb_movie_list = _create_movie_list_for_contest(owner_id=celeb_user.id)
        movie = Movie.objects.get(pk=1)
        celeb_movie_list.movies.add(movie)

        # create a curation for regular user
        movie_list = _create_movie_list_for_contest(owner_id=1)
        movie_list.movies.add(movie)

        # add likes to this new curation list by any user(s)
        movie_list.liked_by.add(celeb_user)
        movie_list.liked_by.add(User.objects.get(pk=1))

        # run the job
        call_command("updatetopcurators")

        # check users position
        res = self.client.get(reverse("api:contest-top-curators", args=["v1", 1]))
        self.assertEqual(200, res.status_code)
        actual_curators = res.json()["results"]
        self.assertEquals(
            [
                {
                    "match": 100.0,
                    "likes_on_recommend": 2,
                    "score": 0.050002,
                    "profile_id": 10,
                    "image": "/default_avatar_m.png",
                    "creator_rank": -1,
                    "curator_rank": -1,
                    "level": 1,
                    "is_celeb": False,
                    "engagement_score": 0.0,
                    "pop_score": 0.0,
                    "city": None,
                    "id": 1,
                    "pos": 1,
                    "name": "Test User",
                }
            ],
            actual_curators,
        )
