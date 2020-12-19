from django.test import TestCase
from django.core import mail
from unittest import mock

from api.models import CrewMember
from api.emails import TEMPLATES
from .base import reverse, APITestCaseMixin


class CrewMemberTestCase(APITestCaseMixin, TestCase):
    fixtures = []

    def test_trigger_email_on_director_add(self):
        pass
