from api.models.payment import Package
from unittest import mock
import os
import json

from django.conf import settings
from django.test import TestCase
from django.core import mail

from api.models import CrewMember, Movie, Genre, MovieLanguage, User
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

    # - select a package for a submitted movie
    # - select a package then select a different package for a submitted movie
    def _select_package(self, pk):
        data = dict(package=pk)
        return self.client.patch(
            reverse("api:order-detail", args=["v1", self.order["id"]]), data
        )

    def setUp(self):
        super().setUp()
        self.movie = self._submit_movie().json()
        self.order = self.movie["order"]
        self.rzp_client_patcher = mock.patch("api.serializers.movie.rzp_client")
        self.rzp_client = self.rzp_client_patcher.start()
        self.rzp_client.order.create.return_value = {
            "status": "created",
            "id": "order_123",
            "amount": 100,
            "receipt": "receipt_123",
        }

    def tearDown(self):
        self.rzp_client_patcher.stop()
        return super().tearDown()

    def _assert_order_is_empty(self, order):
        self.assertIsNotNone(order)
        self.assertIsNotNone(order.owner)
        self.assertIsNone(order.package)
        self.assertIsNone(order.order_id)
        self.assertIsNone(order.amount)
        self.assertIsNone(order.receipt_number)
        self.assertIsNone(order.payment_id)
        self.assertEqual(order.state, "C")

    def _assert_order_is_full(self, order):
        self.assertIsNotNone(order)
        self.assertEquals(order.order_id, "order_123")
        self.assertEquals(order.amount, 100)
        self.assertEquals(order.receipt_number, "receipt_123")
        # still not paid so still "C"
        self.assertEquals(order.state, "C")
        self.assertIsNone(order.payment_id)

    def test_package_selection_after_movie_submit(self):
        movie = Movie.objects.get(id=self.movie["id"])

        # check that a empty order is present (result of a movie submit)
        self.assertEquals(movie.orders.count(), 1)
        order = movie.orders.first()
        self._assert_order_is_empty(order)

        # updating order with package succeeds
        res = self._select_package(1)
        self.assertEquals(res.status_code, 200)

        # verify the order if populated with details
        order.refresh_from_db()
        self._assert_order_is_full(order)
        self.assertEquals(order.package.id, 1)

    def test_create_order_diff_package_success(self):
        """Case where user goes back a step to change package,
        in that case UI should trigger a new order creation with the selected(different) package"""

        movie = Movie.objects.get(id=self.movie["id"])
        # creates an order with package as pack1
        self.test_package_selection_after_movie_submit()

        # confirm that movie has one order with package selected as pack1
        self.assertEquals(movie.orders.count(), 1)
        self.assertIsNotNone(movie.orders.filter(package=1).first())
        self.assertIsNone(movie.orders.filter(package=2).first())

        # creating a new order with different package succeeds
        data = dict(package=2, movie=self.movie["id"])
        res = self.client.post(reverse("api:order-list", args=["v1"]), data)
        self.assertEquals(res.status_code, 201)

        # confirm that another order is created with package as pack2
        movie.refresh_from_db()
        self.assertEquals(movie.orders.count(), 2)
        order = movie.orders.filter(package=2).first()
        self._assert_order_is_full(order)
        self.assertEquals(order.package.id, 2)

    def test_create_order_same_package_fails(self):
        """Case where user goes back a step to change package,
        in that case UI should trigger a new order creation with the selected(different) package"""
        movie = Movie.objects.get(id=self.movie["id"])

        # creates an order with package as pack1
        self.test_package_selection_after_movie_submit()

        # confirm that movie has one order with package selected as pack1
        self.assertEquals(movie.orders.count(), 1)
        self.assertIsNotNone(movie.orders.filter(package=1).first())

        # creating a new order with same package fails
        data = dict(package=1, movie=movie.id)
        res = self.client.post(reverse("api:order-list", args=["v1"]), data)
        self.assertContains(
            res,
            "An order already exists for this movie with this package",
            status_code=400,
        )

    def test_create_order_with_invalid_movie(self):
        data = dict(package=1, movie=10)
        res = self.client.post(reverse("api:order-list", args=["v1"]), data)
        self.assertContains(res, "object does not exist", status_code=400)

    def test_update_order_with_invalid_package(self):
        data = dict(package=10)
        res = self.client.patch(
            reverse("api:order-detail", args=["v1", self.order["id"]]), data
        )
        self.assertContains(res, "object does not exist", status_code=400)

    def test_update_order_with_inactive_package(self):
        pack1 = Package.objects.get(pk=1)
        pack1.active = False
        pack1.save()

        data = dict(package=1)
        res = self.client.patch(
            reverse("api:order-detail", args=["v1", self.order["id"]]), data
        )
        self.assertContains(res, "Invalid Package Selected", status_code=400)

    def test_update_order_with_package_fail(self):
        data = dict(package=1)
        res = self.client.patch(
            reverse("api:order-detail", args=["v1", self.order["id"]]), data
        )
        self.assertEquals(res.status_code, 200)

        data = dict(package=2)
        res = self.client.patch(
            reverse("api:order-detail", args=["v1", self.order["id"]]), data
        )
        self.assertContains(res, "Cannot change Package on an Order", status_code=400)
