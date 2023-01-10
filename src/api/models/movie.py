from logging import getLogger
from django.db import models
from django.contrib.auth.models import User

from api.constants import (
    MOVIE_STATE,
    MOVIE_TYPE,
    REVIEW_STATE,
    CREW_MEMBER_REQUEST_STATE,
)

logger = getLogger("api.models")


class MpGenre(models.Model):
    name = models.CharField(max_length=50, unique=True)
    live = models.BooleanField(default=False)

    def __str__(self):
        return self.name.title()


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
    MOVIE_TYPE_CHOICES = (
        (MOVIE_TYPE.SHORT, "Short Film"),
        (MOVIE_TYPE.BLOG, "Blog"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    # crew members associated with a movie
    crew = models.ManyToManyField(
        "Profile", through="CrewMember", related_name="movies"
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
    genres = models.ManyToManyField(Genre, related_name="movies", blank=True)
    mp_genres = models.ManyToManyField(MpGenre, related_name="movies", blank=True)
    about = models.TextField(blank=True)
    lang = models.ForeignKey(
        MovieLanguage, on_delete=models.SET_NULL, null=True, blank=True
    )
    # to be uploaded by user (Poster)
    poster = models.URLField(null=True, blank=True)
    poster_thumb = models.URLField(null=True, blank=True)
    month = models.DateField(null=True, blank=True)
    # the time at which the movie's state was changed to published
    publish_on = models.DateTimeField(null=True, blank=True)
    jury_rating = models.FloatField(null=True, blank=True, default=0)
    # cached audience rating to be updated periodically
    audience_rating = models.FloatField(null=True, blank=True, default=0)
    # after release model contests become a cached value
    contests = models.ManyToManyField("Contest", related_name="movies", blank=True)

    # cached attributes
    recommend_count = models.IntegerField(default=0)
    review_count = models.IntegerField(default=0)
    # approved by director
    approved = models.BooleanField(
        "Approved by Director", null=True, blank=True, default=None
    )
    type = models.CharField(
        max_length=1, choices=MOVIE_TYPE_CHOICES, default=MOVIE_TYPE.SHORT
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
        return round(score / 2, 1)

    def save(self, *args, **kwargs):
        # TODO: check the change in approved attribute,
        # and send email to owner of the order to inform them that the director
        # has approved the movie submission.
        super().save(*args, **kwargs)


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
        return (
            self.owner.profile.is_celeb
            and self.contest
            and self.contest.name == self.name
        )


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
    rated_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="reviews")
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
    pos = models.IntegerField(default=0)

    class Meta:
        unique_together = [["contest", "profile"]]


class TopCurator(models.Model):
    profile = models.ForeignKey("Profile", on_delete=models.CASCADE)
    contest = models.ForeignKey(
        "Contest", on_delete=models.CASCADE, related_name="top_curators"
    )
    likes_on_recommend = models.IntegerField(default=0)
    match = models.FloatField(default=0)
    # score here is used just for keeping the sort order
    score = models.FloatField(default=0)
    pos = models.IntegerField(default=0)

    class Meta:
        unique_together = [["contest", "profile"]]


class Release(models.Model):
    """Object of this class represents will represent a movie release action,
    since a movie can be released multiple times under different contests.

    NOTE: keeping track of specific order here seem to be useless at the moment,
    since we not interested in knowing for which order a release is being created.
    """

    movie = models.ForeignKey("Movie", on_delete=models.CASCADE)
    contest = models.ForeignKey(
        "Contest", on_delete=models.CASCADE, null=True, blank=True
    )
    on = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # TODO: add a check so that no movie is released more than the sum of releases allowed by all the
        # packages it has purchased
        # if self.movie:
        #     released_count = Release.objects.filter(movie=self.movie).count()
        #     max_releases = 0
        #     if released_count < max_releases:

        super().save(*args, **kwargs)
        if self.movie:
            # update the movie publish date to cache the date of latest release
            self.movie.publish_on = self.on
            self.movie.contests.add(self.contest)
            self.movie.state = MOVIE_STATE.PUBLISHED
            self.movie.save()
