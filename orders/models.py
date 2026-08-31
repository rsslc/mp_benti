from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from decimal import Decimal

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

    # Invoice fields
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text="Auto-generated invoice number (e.g., INV-2025-00001)"
    )
    invoice_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date invoice was generated"
    )

    def __str__(self):
        return f"Order #{self.id} - {self.customer.username}"

    def generate_invoice_number(self):
        """Generate a sequential invoice number in format INV-YYYY-NNNNN"""
        if self.invoice_number:
            return self.invoice_number  # Already has invoice number

        current_year = timezone.now().year
        prefix = f"INV-{current_year}-"

        # Find the highest invoice number for this year
        last_invoice = Order.objects.filter(
            invoice_number__startswith=prefix
        ).order_by('-invoice_number').first()

        if last_invoice and last_invoice.invoice_number:
            # Extract number part and increment
            last_number = int(last_invoice.invoice_number.split('-')[-1])
            new_number = last_number + 1
        else:
            # First invoice of the year
            new_number = 1

        self.invoice_number = f"{prefix}{new_number:05d}"
        self.invoice_date = timezone.now().date()
        self.save()
        return self.invoice_number

    def get_subtotal_ex_gst(self):
        """Calculate order subtotal excluding GST"""
        total = Decimal('0.00')
        for line in self.lines.all():
            if line.unit_price_ex_gst:
                total += line.unit_price_ex_gst * line.quantity
        return total

    def get_total_inc_gst(self):
        """Calculate order total including GST, from each line's actual inc-GST price
        (not all items are GST-applicable, so this can't be a flat 10% of the subtotal)"""
        total = Decimal('0.00')
        for line in self.lines.all():
            total += line.get_line_total_inc_gst()
        return total

    def get_gst_amount(self):
        """Calculate total GST amount actually charged across all lines"""
        return self.get_total_inc_gst() - self.get_subtotal_ex_gst()


class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()

    # Capture prices at order time for accurate historical invoices
    unit_price_ex_gst = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Price per unit excluding GST at time of order"
    )
    unit_price_inc_gst = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Price per unit including GST at time of order"
    )

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def get_line_total_ex_gst(self):
        """Get line total excluding GST"""
        if self.unit_price_ex_gst:
            return self.unit_price_ex_gst * self.quantity
        return Decimal('0.00')

    def get_line_total_inc_gst(self):
        """Get line total including GST, from the actual price captured at order time
        (not a flat 10% — GST-free items have unit_price_inc_gst == unit_price_ex_gst).
        Falls back to the ex-GST total when no inc-GST price was captured, rather than
        guessing a GST rate or silently dropping the line to zero."""
        if self.unit_price_inc_gst is not None:
            return self.unit_price_inc_gst * self.quantity
        return self.get_line_total_ex_gst()

    def get_line_gst(self):
        """Get GST amount actually charged for this line (never negative)"""
        gst = self.get_line_total_inc_gst() - self.get_line_total_ex_gst()
        return gst if gst > 0 else Decimal('0.00')
