from logging import getLogger

from django.db import models
from django.contrib.auth.models import User

from api.constants import MOVIE_STATE, ORDER_STATE
from api.email import TEMPLATES, email_trigger


logger = getLogger(__name__)


class Package(models.Model):
    """Packages cannot be deleted, they can only be made inactive"""

    active = models.BooleanField(default=True)
    name = models.CharField(max_length=50, unique=True)
    amount = models.FloatField()
    attributes = models.ManyToManyField(
        "PackageAttribute", through="PackageAttributeValue"
    )
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name.title()


class PackageAttribute(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class PackageAttributeValue(models.Model):
    package = models.ForeignKey("Package", on_delete=models.CASCADE)
    attribute = models.ForeignKey(
        "PackageAttribute", on_delete=models.CASCADE, related_name="value"
    )
    value = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.package.name}: {self.value}"


class Order(models.Model):
    ORDER_STATES = (
        (ORDER_STATE.CREATED, "Created"),
        (ORDER_STATE.SUBMITTED, "Submitted"),
        (ORDER_STATE.REJECTED, "Rejected"),
    )
    order_id = models.CharField(max_length=100, null=True, blank=True)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    receipt_number = models.CharField(max_length=32, null=True, blank=True)
    amount = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    package = models.ForeignKey(
        "Package", on_delete=models.CASCADE, null=True, blank=True
    )
    # a movie can have multiple active packages at the same time
    # AND an order can have multiple movies in case of one got rejected by the MP Teams
    movies = models.ManyToManyField("Movie", related_name="orders")

    # adding state for the ability to reject orders, cases where a user create way too many valid order
    # effectively taking part in every possible contest
    state = models.CharField(
        choices=ORDER_STATES, max_length=1, default=ORDER_STATE.CREATED
    )

    def __str__(self):
        return f"{self.order_id} - {'C' if self.payment_id else 'P'}"

    def save(self, **kwargs):
        old_payment_id = None
        if self.id:
            old_order = Order.objects.get(id=self.id)
            old_payment_id = old_order.payment_id
        super().save(**kwargs)
        new_payment_id = self.payment_id
        has_completed_payment = bool(not old_payment_id and new_payment_id)
        logger.info(f"payment complete: {has_completed_payment}")
        # TODO: detect the case where user is adding a new movie but not making a new payment (utilizing his credit) and
        # update the movie state and trigger emails
        if has_completed_payment:
            self.state = ORDER_STATE.SUBMITTED
            super().save(**kwargs)
            movies = self._update_movies_state()
            self._trigger_submit_email(movies)

    def _update_movies_state(self):
        # possible 2 scenarios:
        # 1 - new movie new order 1 to 1 - simple case  (1 newly movie in CREATED state)
        # 2 - new movie old order 2 to 1 - using credit case (1 old movie in REJECTED state, 1 new movie in CREATED state),
        # 3 - handles future use case of having multiple movies under one order (multiple new movie in CREATED state)
        # as of now we should have only one movie with CREATED state in self.movies
        # however the logic should work for all the above scenarios
        created_movies = self.movies.filter(state=MOVIE_STATE.CREATED).all()
        for movie in created_movies:
            movie.state = MOVIE_STATE.SUBMITTED
            movie.save()
        return created_movies

    def _trigger_submit_email(self, movies):
        for movie in movies:
            director = (
                movie.crewmember_set.filter(role__name="Director").first().profile.user
            )
            email_trigger(self.owner, TEMPLATES.WELCOME_MDFF, movie=movie)
            if director == self.owner:
                logger.debug("Submission by Director")
                # email_trigger(director, TEMPLATES.SUBMIT_CONFIRM_DIRECTOR)
            else:
                logger.debug("Submission by crew member")
                email_trigger(director, TEMPLATES.DIRECTOR_APPROVAL, movie=movie)
                # email_trigger(self.owner, TEMPLATES.SUBMIT_CONFIRM_CREW)
