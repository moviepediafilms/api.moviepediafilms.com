from logging import getLogger
from django.db import models
from django.contrib.auth.models import User

from api.constants import (
    MOVIE_STATE,
    REVIEW_STATE,
    CREW_MEMBER_REQUEST_STATE,
)

logger = getLogger("api.models")


class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name.title()


class MovieLanguage(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name.title()


class MoviePoster(models.Model):
    link = models.URLField(max_length=200)
    primary = models.BooleanField()
    movie = models.ForeignKey("Movie", on_delete=models.CASCADE)


class Movie(models.Model):
    MOVIE_STATE_CHOICES = (
        (MOVIE_STATE.CREATED, "Created"),
        (MOVIE_STATE.SUBMITTED, "Submitted"),
        (MOVIE_STATE.REJECTED, "Rejected"),
        (MOVIE_STATE.PUBLISHED, "Published"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(
        "Order", on_delete=models.CASCADE, null=True, blank=True, related_name="movies"
    )
    # crew members associated with a movie
    crew = models.ManyToManyField(
        "Profile", through="CrewMember", related_name="movies"
    )
    package = models.ForeignKey(
        "Package", on_delete=models.SET_NULL, null=True, blank=True
    )
    state = models.CharField(max_length=1, choices=MOVIE_STATE_CHOICES)
    title = models.CharField(max_length=100)
    link = models.URLField(
        null=False,
        blank=False,
        unique=True,
        error_messages={"unique": "This film already exist on our platform"},
    )
    # in minutes
    runtime = models.FloatField()
    genres = models.ManyToManyField(Genre)
    about = models.TextField(blank=True)
    lang = models.ForeignKey(
        MovieLanguage, on_delete=models.SET_NULL, null=True, blank=True
    )
    # to be uploaded by user (Poster)
    poster = models.URLField(null=True, blank=True)
    month = models.DateField(null=True, blank=True)
    # the time at which the movie's state was changed to published
    publish_on = models.DateTimeField(null=True, blank=True)
    jury_rating = models.FloatField(null=True, blank=True, default=0)
    # cached audience rating to be updated periodically
    audience_rating = models.FloatField(null=True, blank=True, default=0)
    contest = models.ForeignKey(
        "Contest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movies",
    )

    # cached attributes
    recommend_count = models.IntegerField(default=0)
    review_count = models.IntegerField(default=0)
    # approved by director
    approved = models.BooleanField(
        "Approved by Director", null=True, blank=True, default=None
    )

    class Meta:
        ordering = ["publish_on"]

    def __str__(self):
        return self.title

    def is_live(self):
        return self.contest and self.contest.is_live()

    def score(self):
        score = self.audience_rating or 0
        score += self.jury_rating or 0
        return score / 2

    # TODO: override save to check the change in approved attribute,
    # and send email to owner of the order to inform them that the director
    # has approved the movie submission.


class CrewMember(models.Model):
    movie = models.ForeignKey("Movie", on_delete=models.CASCADE)
    profile = models.ForeignKey("Profile", on_delete=models.CASCADE)
    role = models.ForeignKey("Role", on_delete=models.CASCADE)

    class Meta:
        # one person(profile) cannot be a Director(Role) multiple times in a movie
        unique_together = [["movie", "profile", "role"]]


class CrewMemberRequest(models.Model):
    CREW_MEMBER_CHOICES = [
        (CREW_MEMBER_REQUEST_STATE.SUBMITTED, "Submitted"),
        (CREW_MEMBER_REQUEST_STATE.APPROVED, "Approved"),
        (CREW_MEMBER_REQUEST_STATE.DECLINED, "Declined"),
    ]
    requestor = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey("Movie", on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="in_crewmemberrequest"
    )
    role = models.ForeignKey("Role", on_delete=models.CASCADE)
    state = models.CharField(
        max_length=1,
        choices=CREW_MEMBER_CHOICES,
        default=CREW_MEMBER_REQUEST_STATE.SUBMITTED,
    )
    reason = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["requestor", "movie", "user", "role"]]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        logger.debug("crew_membership changed")

        if self.state == CREW_MEMBER_REQUEST_STATE.APPROVED:
            cm, _ = CrewMember.objects.get_or_create(
                movie=self.movie, profile=self.user.profile, role=self.role
            )
            logger.info(f"{cm} a crew membership was approved and added to movie")


class MovieList(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    movies = models.ManyToManyField("Movie", related_name="in_lists", blank=True)
    name = models.CharField(max_length=50)
    liked_by = models.ManyToManyField(User, related_name="liked_lists", blank=True)
    frozen = models.BooleanField(default=False)
    contest = models.ForeignKey(
        "Contest",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="movie_lists",
    )

    class Meta:
        unique_together = [["owner", "name"]]

    def is_celeb_recommends(self):
        return self.owner.is_celeb and self.contest and self.contest.name == self.name


class Visits(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    source = models.ForeignKey(MovieList, on_delete=models.CASCADE)


class MovieRateReview(models.Model):
    REVIEW_STATE_CHOICES = [
        (REVIEW_STATE.PUBLISHED, "Published"),
        (REVIEW_STATE.BLOCKED, "Blocked"),
    ]
    state = models.CharField(choices=REVIEW_STATE_CHOICES, max_length=1)
    published_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    # is nullable since user might only rate and not write the review at all
    content = models.TextField(null=True, blank=True)
    # is nullable since user might review the movie first before rating or may choose to not rate at all
    rating = models.FloatField(null=True, blank=True)
    liked_by = models.ManyToManyField(User, related_name="liked_reviews", blank=True)

    class Meta:
        unique_together = [["movie", "author"]]


class TopCreator(models.Model):
    profile = models.ForeignKey("Profile", on_delete=models.CASCADE)
    contest = models.ForeignKey(
        "Contest", on_delete=models.CASCADE, related_name="top_creators"
    )
    recommend_count = models.IntegerField(default=0)
    score = models.FloatField(default=0)


class TopCurator(models.Model):
    profile = models.ForeignKey("Profile", on_delete=models.CASCADE)
    contest = models.ForeignKey(
        "Contest", on_delete=models.CASCADE, related_name="top_curators"
    )
    recommend_count = models.IntegerField(default=0)
    match = models.FloatField(default=0)
