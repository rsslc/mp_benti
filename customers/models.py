from django.contrib.auth.models import User
from django.db import models


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    business_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(
        blank=True,
        help_text="Customer delivery/billing address (street, city, state, postcode)"
    )

    def __str__(self):
        return self.business_name
