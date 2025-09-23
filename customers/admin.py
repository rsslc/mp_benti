from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("business_name", "user", "phone")
    search_fields = ("business_name", "user__username", "user__email")
