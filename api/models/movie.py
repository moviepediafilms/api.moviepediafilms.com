from django.db import models
from django.contrib.auth.models import User
from api.constants import MOVIE_STATE

MOVIE_STATE_CHOICES = (
    (MOVIE_STATE.SUBMITTED, "Submitted"),
    (MOVIE_STATE.PUBLISHED, "Published"),
    (MOVIE_STATE.HIDDEN, "Hidden"),
    (MOVIE_STATE.ARCHIVED, "Archived"),
)


class MovieGenre(models.Model):
    name = models.CharField(max_length=50)


class MovieExternalAward(models.Model):
    name = models.CharField(max_length=100)


class MovieFrame(models.Model):
    url = models.URLField()


class MovieLanguage(models.Model):
    name = models.CharField(max_length=50)


class Movie(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=1, choices=MOVIE_STATE_CHOICES)
    name = models.CharField(max_length=100)
    link = models.URLField()
    runtime = models.FloatField()
    genre = models.ManyToManyField(MovieGenre)
    awards = models.ManyToManyField(MovieExternalAward)
    about = models.TextField()
    lan = models.ForeignKey(MovieLanguage, on_delete=models.CASCADE)
    # to be uploaded by user (Poster)
    thumb = models.URLField()
    month = models.DateField()
    frames = models.ManyToManyField(MovieFrame)
    # the time at which the movie's state was changed to published
    publish_on = models.DateTimeField(null=True, blank=True)
    jury_rating = models.FloatField()

    # director is either the user himself or he gives the info about him
    # one out of these two info should be present
    director = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    director_name = models.CharField(max_length=100, null=True, blank=True)
    director_email = models.CharField(max_length=50, null=True, blank=True)
    director_mob = models.CharField(max_length=20, null=True, blank=True)


class MovieUserRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rating = models.FloatField()


class MovieReview(models.Model):
    published_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    liked_by = models.ManyToManyField(User)
