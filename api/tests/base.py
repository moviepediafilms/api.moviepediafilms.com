from functools import partial

from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from api.models import User

reverse = partial(reverse, args=["v1"])


class APITestCaseMixin:
    client_class = APIClient


class LoggedInMixin:
    auth_user_id = 1

    def setUp(self):
        super().setUp()
        token, _ = Token.objects.get_or_create(user_id=self.auth_user_id)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        self.user = User.objects.get(pk=self.auth_user_id)
        self.profile = self.user.profile
