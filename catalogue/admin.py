from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "get_products_count", "has_image")
    list_filter = ("parent",)
    search_fields = ("name", "description")
    autocomplete_fields = ("parent",)
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'parent')
        }),
        ('Image', {
            'fields': ('image',),
            'description': 'Upload an image to represent this category'
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent')

    def get_products_count(self, obj):
        return obj.products.count()
    get_products_count.short_description = "Products"

    def has_image(self, obj):
        return "✓" if obj.image else "✗"
    has_image.short_description = "Image"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            kwargs["queryset"] = Category.objects.filter(parent=None)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "unit",
        "pack_size",
        "price_ex_gst",
        "price_inc_gst",
        "available",
        "stock_quantity",
    )
    list_filter = ("category", "available")
    search_fields = ("name", "description")
