from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.db.models.deletion import CASCADE
from api.constants import (
    MOVIE_STATE,
    REVIEW_STATE,
    CREW_MEMBER_REQUEST_STATE,
    CONTEST_STATE,
)

MOVIE_STATE_CHOICES = (
    (MOVIE_STATE.CREATED, "Created"),
    (MOVIE_STATE.SUBMITTED, "Submitted"),
    (MOVIE_STATE.REJECTED, "Rejected"),
    (MOVIE_STATE.PUBLISHED, "Published"),
)


REVIEW_STATE_CHOICES = [
    (REVIEW_STATE.PUBLISHED, "Published"),
    (REVIEW_STATE.BLOCKED, "Blocked"),
]

CREW_MEMBER_CHOICES = [
    (CREW_MEMBER_REQUEST_STATE.SUBMITTED, "Submitted"),
    (CREW_MEMBER_REQUEST_STATE.APPROVED, "Approved"),
    (CREW_MEMBER_REQUEST_STATE.DECLINED, "Declined"),
]

CONTEST_STATE_CHOICES = [
    (CONTEST_STATE.CREATED, "Created"),
    (CONTEST_STATE.LIVE, "Live"),
    (CONTEST_STATE.FINISHED, "Finished"),
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


class Title(models.Model):
    name = models.CharField(max_length=50)


class ContestWinner(models.Model):
    contest = models.ForeignKey("Contest", on_delete=models.CASCADE)
    profile = models.ForeignKey("Profile", on_delete=models.CASCADE)
    position = models.IntegerField()
    title = models.ForeignKey("Title", on_delete=CASCADE)

    def __str__(self):
        return f"{self.content_id}, {self.profile_id}, {self.position}"


class ContestType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Contest(models.Model):
    name = models.CharField(max_length=100)
    start = models.DateTimeField(auto_now_add=False)
    end = models.DateTimeField(auto_now_add=False)
    days_per_movie = models.IntegerField(default=15)
    type = models.ForeignKey("ContestType", on_delete=models.CASCADE)
    state = models.CharField(
        max_length=1, choices=CONTEST_STATE_CHOICES, default=CONTEST_STATE.CREATED
    )
    winners = models.ManyToManyField("Profile", through="ContestWinner", blank=True)
    max_recommends = models.IntegerField(default=20)

    def __str__(self):
        return self.name

    def is_live(self):
        if self.state == CONTEST_STATE.LIVE:
            now = timezone.now()
            return self.start < now and now < self.end
        else:
            return False


class MoviePoster(models.Model):
    link = models.URLField(max_length=200)
    primary = models.BooleanField()
    movie = models.ForeignKey("Movie", on_delete=models.CASCADE)


class Movie(models.Model):
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
    contest = models.ForeignKey(
        "Contest",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="movies",
    )
    # cached
    recommend_count = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    def is_live(self):
        return self.contest and self.contest.is_live()

    def score(self):
        score = self.audience_rating or 0
        score += self.jury_rating or 0
        return score / 2


class CrewMember(models.Model):
    movie = models.ForeignKey("Movie", on_delete=models.CASCADE)
    profile = models.ForeignKey("Profile", on_delete=models.CASCADE)
    role = models.ForeignKey("Role", on_delete=models.CASCADE)

    class Meta:
        # one person(profile) cannot be a Director(Role) multiple times in a movie
        unique_together = [["movie", "profile", "role"]]


class CrewMemberRequest(models.Model):
    requestor = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey("Movie", on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="in_crewmemberrequest"
    )
    role = models.ForeignKey("Role", on_delete=models.CASCADE)
    state = models.CharField(max_length=1, choices=CREW_MEMBER_CHOICES)
    reason = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["requestor", "movie", "user", "role"]]


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
