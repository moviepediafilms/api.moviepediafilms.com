from django.test import TestCase

# from django.core import mail

# from api.email import TEMPLATES
from .base import reverse, APITestCaseMixin, LoggedInMixin


class FilmographyPrivateDirectorTestCase(APITestCaseMixin, LoggedInMixin, TestCase):
    """user 1 watching user 1's filmography where user 1 is Director"""

    auth_user_id = 1
    fixtures = []


class FilmographyPublicDirectorTestCase(APITestCaseMixin, LoggedInMixin, TestCase):
    """user 2 watching user 1's filmography where user 1 is Director"""

    auth_user_id = 2
    fixtures = []


class FilmographyPrivateCuratorTestCase(APITestCaseMixin, LoggedInMixin, TestCase):
    """user 2 watching user 2's filmography where user 2 is not a Director"""

    auth_user_id = 2
    fixtures = []


class FilmographyPublicCuratorTestCase(APITestCaseMixin, LoggedInMixin, TestCase):
    """user 2 watching user 3's filmography where user 3 is not a Director"""

    auth_user_id = 2
    fixtures = []
