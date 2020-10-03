from django.db import models
from django.contrib.auth.models import User


class Order(models.Model):
    order_id = models.CharField(max_length=100, unique=True)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    receipt_number = models.CharField(max_length=32)
    amount = models.FloatField()
    created_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.order_id
