from unittest import mock
import os
import json

from django.conf import settings
from django.test import TestCase
from django.core import mail

from api.models import CrewMember, Movie, Genre, MovieLanguage, User, Package
from .base import reverse, APITestCaseMixin, LoggedInMixin


class MovieSubmitTestMixin:
    genres = [dict(name="Drama")]
    lang = dict(name="English")
    runtime = 12
    director = None

    def _submit_movie(self, check_success=True):
        res = None
        poster_file_path = "api/tests/test_poster.png"
        self.assertTrue(os.path.exists(poster_file_path))
        data = dict(
            payload=dict(
                title="Movie1",
                link="http://google.com",
                lang=self.lang,
                runtime=self.runtime,
                roles=self.roles,
                genres=self.genres,
            )
        )
        if self.director:
            data["payload"]["director"] = self.director
        with open(poster_file_path, "rb") as poster_fh:
            data["poster"] = poster_fh
            data["payload"] = json.dumps(data["payload"])
            res = self.client.post(reverse("api:submit-list"), data, format="multipart")
        if check_success:
            self.assertEquals(201, res.status_code, res.content)
        return res


class BasicMovieTestMixin(MovieSubmitTestMixin):
    def test_no_emails_sent(self):
        self._submit_movie()
        self.assertEqual(0, len(mail.outbox))

    def test_poster_saved(self):
        poster_file_path = "api/tests/test_poster.png"
        res = self._submit_movie()
        movie_json = res.json()
        uploaded_poster_rel_path = movie_json["poster"]
        uploaded_poster_abs_path = os.path.join(
            settings.MEDIA_ROOT, uploaded_poster_rel_path.lstrip("/media")
        )
        self.assertTrue(
            os.path.exists(uploaded_poster_abs_path),
            "Uploaded poster was not found on disk",
        )
        self.assertEquals(
            os.path.getsize(uploaded_poster_abs_path),
            os.path.getsize(poster_file_path),
        )

    def test_genres_added(self):
        res = self._submit_movie()
        movie_id = res.json()["id"]
        movie = Movie.objects.get(pk=movie_id)
        for genre in self.genres:
            genre = Genre.objects.get(name=genre.get("name").lower())
            self.assertIn(
                genre, movie.genres.all(), f"{genre.name} is not added to movie"
            )

    def test_lang_added(self):
        res = self._submit_movie()
        movie_id = res.json()["id"]
        movie = Movie.objects.get(pk=movie_id)
        self.assertEquals(
            movie.lang, MovieLanguage.objects.get(name=self.lang.get("name"))
        )

    def test_runtime(self):
        res = self._submit_movie()
        movie_id = res.json()["id"]
        movie = Movie.objects.get(pk=movie_id)
        self.assertEquals(movie.runtime, self.runtime)


class SubmissionByDirectorTestCase(
    LoggedInMixin, APITestCaseMixin, TestCase, BasicMovieTestMixin
):
    fixtures = ["test_submission.yaml"]
    roles = [dict(name="Director"), dict(name="Actor")]

    def test_is_approved(self):
        res = self._submit_movie()
        movie_id = res.json()["id"]
        movie = Movie.objects.get(pk=movie_id)
        self.assertTrue(movie.approved)

    def test_roles_added(self):
        res = self._submit_movie()
        movie_id = res.json()["id"]
        movie = Movie.objects.get(pk=movie_id)
        for role in self.roles:
            self.assertTrue(
                CrewMember.objects.filter(
                    movie=movie, role__name=role.get("name"), profile=self.profile
                ).exists()
            )


class SubmissionUnregisteredDirectorTestCase(
    LoggedInMixin, APITestCaseMixin, TestCase, BasicMovieTestMixin
):
    fixtures = ["test_submission.yaml"]

    roles = [dict(name="Actor")]
    director = dict(
        first_name="Test3",
        last_name="User",
        email="test3@example.com",
        contact="1234567890",
    )

    def test_director_profile_created(self):
        users_count = User.objects.count()
        self._submit_movie()
        self.assertEquals(User.objects.count(), users_count + 1)

    def test_director_not_onboarded(self):
        res = self._submit_movie()
        movie_id = res.json()["id"]
        movie = Movie.objects.get(id=movie_id)
        crewmember = CrewMember.objects.get(movie=movie, role__name="Director")
        self.assertFalse(crewmember.profile.onboarded)

    def test_movie_not_approved(self):
        res = self._submit_movie()
        movie_id = res.json()["id"]
        movie = Movie.objects.get(id=movie_id)
        self.assertFalse(movie.approved)


class SubmissionRegisteredDirectorTestCase(
    LoggedInMixin, APITestCaseMixin, TestCase, BasicMovieTestMixin
):
    fixtures = ["test_submission.yaml"]

    roles = [dict(name="Actor")]
    director = dict(
        first_name="Test3",
        last_name="User",
        email="test2@example.com",
        contact="1234567890",
    )

    def test_no_new_profiles_created(self):
        before_users_count = User.objects.count()
        self._submit_movie()
        after_users_count = User.objects.count()
        self.assertEquals(before_users_count, after_users_count)

    def test_movie_not_approved(self):
        res = self._submit_movie()
        movie_id = res.json()["id"]
        movie = Movie.objects.get(id=movie_id)
        self.assertFalse(movie.approved)


class SubmissionNoDirectorTestCase(
    LoggedInMixin, APITestCaseMixin, TestCase, MovieSubmitTestMixin
):
    fixtures = ["test_submission.yaml"]
    roles = [dict(name="Actor")]

    def test_error_if_no_director(self):
        res = self._submit_movie(check_success=False)
        self.assertEquals(400, res.status_code)
        self.assertIn("Director must be provided", res.content.decode())


class SubmissionPackageSelectionTestCase(
    LoggedInMixin, APITestCaseMixin, TestCase, MovieSubmitTestMixin
):
    fixtures = ["test_submission.yaml"]
    roles = [dict(name="Director")]
    package = dict(name="pack1")

    def _select_package(self):
        data = dict(payload=json.dumps(dict(package=self.package)))
        return self.client.patch(
            reverse("api:submit-detail", args=["v1", self.movie["id"]]),
            data,
            format="multipart",
        )

    def setUp(self):
        super().setUp()
        self.movie = self._submit_movie().json()

    @mock.patch("api.serializers.movie.rzp_client")
    def test_package_attached_to_movie(self, rzp_client):
        rzp_client.order.create.return_value = {
            "status": "created",
            "id": "order_123",
            "amount": 100,
            "receipt": "receipt_123",
        }
        movie = Movie.objects.get(id=self.movie["id"])
        self.assertIsNone(movie.package)
        res = self._select_package()
        self.assertEquals(200, res.status_code)
        movie.refresh_from_db()
        self.assertIsNotNone(movie.package)
        self.assertEquals(movie.package, Package.objects.filter(**self.package).first())
