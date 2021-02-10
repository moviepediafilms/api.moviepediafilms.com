from api.constants import MOVIE_STATE
from django.core.management import call_command
from django.test import TestCase
from api.models import Movie, MovieList
from .base import APITestCaseMixin


class CommandTestCase(TestCase, APITestCaseMixin):
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
        "movielist",
    ]

    def test_count_personal_and_contest_recommend(self):
        movie = Movie.objects.get(pk=1)
        self.assertEquals(0, movie.recommend_count)
        movie = Movie.objects.get(pk=1)
        MovieList.objects.get(pk=1).movies.add(movie)
        MovieList.objects.get(pk=2).movies.add(movie)
        call_command("updatemovierecommends")
        movie.refresh_from_db()
        self.assertEquals(2, movie.recommend_count)

    def test_ignore_non_published_movies(self):
        movie = Movie.objects.get(pk=1)
        self.assertEquals(0, movie.recommend_count)
        movie.state = MOVIE_STATE.SUBMITTED
        movie.save()
        MovieList.objects.get(pk=1).movies.add(movie)
        call_command("updatemovierecommends")
        movie.refresh_from_db()
        self.assertEquals(0, movie.recommend_count)
