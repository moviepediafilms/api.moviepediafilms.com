from django.test import TestCase
from django.core import mail
from unittest import mock


from api.models import User
from api.email import TEMPLATES
from .base import reverse, APITestCaseMixin


class WithPayloadMixin:
    def setUp(self):
        self.payload = {
            "user": {
                "email": "abcd@example.com",
                "password": "123456",
                "first_name": "Test",
                "last_name": "User",
            },
            "dob": "2020-12-12",
            "gender": "M",
            "mobile": "123456789012",
        }
        self.expected = {
            "about": None,
            "city": None,
            "engagement_score": 0.0,
            "follows": [],
            "gender": "M",
            "id": 1,
            "image": "/default_avatar_m.png",
            "level": 1,
            "mcoins": 0.0,
            "is_celeb": False,
            "movies_directed": 0,
            "name": "Test User",
            "pop_score": 0.0,
            "profile_id": 1,
            "creator_rank": -1,
            "curator_rank": -1,
            "roles": [],
            "title": None,
        }


class SignUpTestCase(APITestCaseMixin, WithPayloadMixin, TestCase):
    def test_signup_ok(self):
        res = self.client.post(reverse("api:profile-list"), data=self.payload)
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].template_id, TEMPLATES.VERIFY)
        self.assertEquals(res.status_code, 201)
        self.assertEquals(res.json(), self.expected)
        user = User.objects.get(pk=1)
        self.assertFalse(user.is_active)

    def test_signup_password_error(self):
        self.payload["user"]["password"] = "1223"
        res = self.client.post(reverse("api:profile-list"), data=self.payload)
        self.assertEquals(len(mail.outbox), 0)
        self.assertEquals(res.status_code, 400)
        self.assertEquals(
            res.json(),
            {"user": {"password": ["Ensure this field has at least 6 characters."]}},
        )


class SignInTestCase(APITestCaseMixin, WithPayloadMixin, TestCase):
    fixtures = ["test_auth"]

    def test_signup_partial(self):
        profile_id = 1
        del self.payload["user"]["email"]
        self.payload["token"] = "token-abcd"

        res = self.client.patch(
            reverse("api:profile-detail", args=["v1", profile_id]),
            data=self.payload,
        )
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].template_id, TEMPLATES.VERIFY)
        self.assertEquals(res.status_code, 200)
        self.assertEquals(res.json(), self.expected)

    def test_inactive_login_fail(self):
        user = User.objects.get(pk=1)
        self.assertFalse(user.is_active)
        res = self.client.post(
            reverse("api:login"), {"username": "test@example.com", "password": "1234"}
        )
        self.assertEquals(400, res.status_code)
        self.assertEquals(
            {
                "non_field_errors": [
                    "Your account is not active, please verify your account before login"
                ]
            },
            res.json(),
        )
        self.assertEquals(len(mail.outbox), 0)

    def test_active_login_ok(self):
        user = User.objects.get(pk=1)
        self.assertFalse(user.is_active)
        res = self.client.post(
            reverse("api:login"), {"username": "test2@example.com", "password": "admin"}
        )
        self.assertEquals(res.status_code, 200)
        self.assertEquals(
            {
                "email": "test2@example.com",
                "token": "token2-abcd",
                "user_id": 2,
            },
            res.json(),
        )
        self.assertEquals(len(mail.outbox), 0)

    def test_activate_account(self):
        user = User.objects.get(pk=1)
        self.assertFalse(user.is_active)
        res = self.client.get(reverse("api:account-verify", args=["v1", "token-abcd"]))
        self.assertEquals(res.status_code, 200)
        self.assertEquals(res.json(), {"success": True})
        self.assertEquals(len(mail.outbox), 0)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_verification_resend_inactive(self):
        res = self.client.post(
            reverse("api:account-resend"), {"email": "test@example.com"}
        )
        self.assertEqual(200, res.status_code)
        self.assertEqual({"success": True}, res.json())

    def test_verification_resend_active(self):
        res = self.client.post(
            reverse("api:account-resend"), {"email": "test2@example.com"}
        )
        self.assertEqual(400, res.status_code)
        self.assertEqual(
            {
                "non_field_errors": [
                    "The account is already active. Please login or click on forgot password"
                ]
            },
            res.json(),
        )

    def test_forgot_password_email_trigger(self):
        with mock.patch("api.serializers.auth.requests") as requests:
            requests.post.return_value.json.return_value = {"success": True}
            res = self.client.post(
                reverse("api:account-forgot"),
                {"email": "test2@example.com", "recaptcha": "recaptcha-1234"},
            )
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].template_id, TEMPLATES.PASSWORD_RESET)
        self.assertEquals(["test2@example.com"], mail.outbox[0].to)

    def test_reset_password_ok(self):
        user = User.objects.get(pk=2)
        self.assertFalse(user.check_password("xxyyzz"))
        res = self.client.post(
            reverse("api:account-reset", args=["v1", "token2-abcd"]),
            {"password": "xxyyzzz"},
        )
        self.assertEqual(200, res.status_code)
        user.refresh_from_db()
        self.assertTrue(user.check_password("xxyyzzz"))
