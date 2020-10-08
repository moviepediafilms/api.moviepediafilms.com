from django.db import models
from django.contrib.auth.models import User


class Package(models.Model):
    name = models.CharField(max_length=50, unique=True)
    amount = models.FloatField()


class Order(models.Model):
    order_id = models.CharField(max_length=100, null=True, blank=True)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    receipt_number = models.CharField(max_length=32, null=True, blank=True)
    amount = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.order_id
