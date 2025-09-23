from django.db import models
from django.core.cache import cache


class SiteSettings(models.Model):
    """Singleton model for site-wide settings"""
    show_prices = models.BooleanField(
        default=True,
        help_text="Enable/disable price display across the entire site"
    )
    price_hidden_message = models.CharField(
        max_length=200,
        default="Contact us for pricing",
        help_text="Message to show when prices are hidden"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return "Site Settings"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.__class__.objects.exclude(id=self.id).delete()

        # Clear cache when settings change
        cache.delete('site_settings')

        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get the singleton settings instance, cached for performance"""
        settings = cache.get('site_settings')
        if settings is None:
            settings, created = cls.objects.get_or_create(id=1)
            cache.set('site_settings', settings, 300)  # Cache for 5 minutes
        return settings