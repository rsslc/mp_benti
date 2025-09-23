from django.contrib.auth.models import User
from django.db import models

from catalogue.models import Product


ORDER_STATUS = (
    ("new", "New"),
    ("processing", "Processing"),
    ("fulfilled", "Fulfilled"),
)


class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default="new")
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.username}"


class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
