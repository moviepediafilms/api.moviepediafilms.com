from logging import getLogger

from django.db import models
from django.contrib.auth.models import User

from api.constants import MOVIE_STATE
from api.emails import TEMPLATES, email_trigger


logger = getLogger(__name__)


class Package(models.Model):
    name = models.CharField(max_length=50, unique=True)
    amount = models.FloatField()

    def __str__(self):
        return self.name.title()


class Order(models.Model):
    order_id = models.CharField(max_length=100, null=True, blank=True)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    receipt_number = models.CharField(max_length=32, null=True, blank=True)
    amount = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")

    def __str__(self):
        return f"{self.order_id} - {'C' if self.payment_id else 'P'}"

    def save(self, **kwargs):
        logger.info("order updated")
        old_payment_id = None
        if self.id:
            old_order = Order.objects.get(id=self.id)
            old_payment_id = old_order.payment_id
        super().save(**kwargs)
        new_payment_id = self.payment_id
        has_completed_payment = bool(not old_payment_id and new_payment_id)
        logger.info(f"order updated has_completed_payment: {has_completed_payment}")
        if has_completed_payment:
            # for cases when credits are being used by the user - only one movie under this order can have state CREATED
            movie = self.movies.filter(state=MOVIE_STATE.CREATED).first()
            movie.state = MOVIE_STATE.SUBMITTED
            movie.save()
            director = (
                movie.crewmember_set.filter(role__name="Director").first().profile.user
            )
            if director == self.owner:
                logger.debug("Submission by Director")
                email_trigger(director, TEMPLATES.SUBMIT_CONFIRM_DIRECTOR)
            else:
                logger.debug("Submission by crew member")
                email_trigger(director, TEMPLATES.DIRECTOR_APPROVAL)
                email_trigger(self.owner, TEMPLATES.SUBMIT_CONFIRM_CREW)
