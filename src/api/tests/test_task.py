from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from api.models.contest import ContestType
from api.constants import CONTEST_STATE, MOVIE_STATE
from api.models import Release, Movie, Contest
from api.tasks import create_poster_thumb


class TasksTestCase(TestCase):
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

    def setUp(self):
        super().setUp()

    def test_generate_thumb(self):
        movie = Movie.objects.all()[0]
        create_poster_thumb(movie.id)
