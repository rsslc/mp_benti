from django.contrib import admin
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from .models import SiteSettings


def is_superuser(user):
    return user.is_superuser


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'show_prices', 'updated_at')
    fieldsets = (
        ('Price Display Settings', {
            'fields': ('show_prices', 'price_hidden_message'),
            'description': 'Control whether prices are displayed across the site'
        }),
    )

    @method_decorator(user_passes_test(is_superuser))
    def changelist_view(self, request, extra_context=None):
        return super().changelist_view(request, extra_context=extra_context)

    @method_decorator(user_passes_test(is_superuser))
    def change_view(self, request, object_id, form_url='', extra_context=None):
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def has_add_permission(self, request):
        # Only allow one instance
        return not SiteSettings.objects.exists() and request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False  # Prevent deletion of settings