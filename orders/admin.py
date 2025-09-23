from django.contrib import admin

from .models import Order, OrderLine


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "created_at", "status")
    list_filter = ("status", "created_at")
    search_fields = ("customer__username", "customer__email")
    inlines = [OrderLineInline]
