from django.db import models
from django.contrib.auth.models import User
from api.constants import MOVIE_STATE, REVIEW_STATE

MOVIE_STATE_CHOICES = (
    (MOVIE_STATE.SUBMITTED, "Submitted"),
    (MOVIE_STATE.REJECTED, "Rejected"),
    (MOVIE_STATE.PUBLISHED, "Published"),
    (MOVIE_STATE.HIDDEN, "Hidden"),
    (MOVIE_STATE.ARCHIVED, "Archived"),
)


REVIEW_STATE_CHOICES = [
    (REVIEW_STATE.PUBLISHED, "Published"),
    (REVIEW_STATE.BLOCKED, "Blocked"),
]


class MovieGenre(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name.title()


class MovieFrame(models.Model):
    url = models.URLField()


class MovieLanguage(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name.title()


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
    # the time at which the movie's state was changed to published
    publish_on = models.DateTimeField(null=True, blank=True)
    jury_rating = models.FloatField(null=True, blank=True, default=0)
    # cached audience rating to be updated periodically
    audience_rating = models.FloatField(null=True, blank=True, default=0)


class CrewMember(models.Model):
    movie = models.ForeignKey("Movie", on_delete=models.CASCADE)
    profile = models.ForeignKey("Profile", on_delete=models.CASCADE)
    role = models.ForeignKey("Role", on_delete=models.CASCADE)

    unique_together = [["movie", "profile", "role"]]


class MovieList(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    movies = models.ManyToManyField("Movie", related_name="in_lists", blank=True)
    name = models.CharField(max_length=50)
    liked_by = models.ManyToManyField(User, related_name="liked_lists", blank=True)

    unique_together = [["owner", "name"]]


class Visits(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    source = models.ForeignKey(MovieList, on_delete=models.CASCADE)


class MovieRateReview(models.Model):
    state = models.CharField(choices=REVIEW_STATE_CHOICES, max_length=1)
    published_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    # is nullable since user might only rate and not write the review at all
    content = models.TextField(null=True, blank=True)
    # is nullable since user might review the movie first before rating or may choose to not rate at all
    rating = models.FloatField(null=True, blank=True)
    liked_by = models.ManyToManyField(User, related_name="liked_reviews", blank=True)
    # TODO: enable unique constrains before finalizing
    unique_together = [["movie", "author"]]
