from django.db import models
from django.contrib.auth.models import User
from api.constants import MOVIE_STATE

MOVIE_STATE_CHOICES = (
    (MOVIE_STATE.SUBMITTED, "Submitted"),
    (MOVIE_STATE.REJECTED, "Rejected"),
    (MOVIE_STATE.PUBLISHED, "Published"),
    (MOVIE_STATE.HIDDEN, "Hidden"),
    (MOVIE_STATE.ARCHIVED, "Archived"),
)


class MovieGenre(models.Model):
    name = models.CharField(max_length=50, unique=True)


class MovieFrame(models.Model):
    url = models.URLField()


class MovieLanguage(models.Model):
    name = models.CharField(max_length=50, unique=True)


class MoviePoster(models.Model):
    link = models.URLField(max_length=200)
    primary = models.BooleanField()
    movie = models.ForeignKey("Movie", on_delete=models.CASCADE)


class Movie(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey("Order", on_delete=models.CASCADE, null=True, blank=True)
    # crew members associated with a movie
    crew = models.ManyToManyField("Profile", through="CrewMember")
    package = models.ForeignKey(
        "Package", on_delete=models.SET_NULL, null=True, blank=True
    )
    state = models.CharField(max_length=1, choices=MOVIE_STATE_CHOICES)
    title = models.CharField(max_length=100)
    link = models.URLField()
    # in minutes
    runtime = models.FloatField()
    genres = models.ManyToManyField(MovieGenre)
    about = models.TextField()
    lang = models.ForeignKey(MovieLanguage, on_delete=models.CASCADE)
    # to be uploaded by user (Poster)
    poster = models.URLField(null=True, blank=True)
    month = models.DateField(null=True, blank=True)
    frames = models.ManyToManyField(MovieFrame, blank=True)
    # the time at which the movie's state was changed to published
    publish_on = models.DateTimeField(null=True, blank=True)
    jury_rating = models.FloatField(null=True, blank=True)
    # cached audience rating to be updated periodically
    audience_rating = models.FloatField(null=True, blank=True)


class CrewMember(models.Model):
    movie = models.ForeignKey("Movie", on_delete=models.CASCADE)
    profile = models.ForeignKey("Profile", on_delete=models.CASCADE)
    role = models.ForeignKey("Role", on_delete=models.CASCADE)

    unique_together = [["movie", "profile", "role"]]


class MovieUserRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rating = models.FloatField()


class MovieReview(models.Model):
    published_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    liked_by = models.ManyToManyField(User)
