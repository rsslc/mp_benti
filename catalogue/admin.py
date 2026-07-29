from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
import csv
import io
import os

from .models import Category, Product
from .utils import get_import_image_file


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
        "pack_description",
        "price_ex_gst",
        "price_inc_gst",
        "available",
        "stock_quantity",
    )
    list_filter = ("category", "available")
    search_fields = ("name", "description")
    actions = ['export_to_csv', 'delete_selected']

    def export_to_csv(self, request, queryset):
        """Export selected products to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products_export.csv"'

        writer = csv.writer(response)
        # Write header
        writer.writerow([
            'Name', 'Category', 'Description', 'Pack Description',
            'Price Ex GST', 'Price Inc GST', 'Available', 'Stock Quantity',
            'Image', 'Alt Image'
        ])

        # Write data
        for product in queryset:
            writer.writerow([
                product.name,
                product.category.name,
                product.description,
                product.pack_description,
                product.price_ex_gst,
                product.price_inc_gst,
                product.available,
                product.stock_quantity,
                os.path.basename(product.image_main.name) if product.image_main else '',
                os.path.basename(product.image_alt.name) if product.image_alt else '',
            ])

        return response
    export_to_csv.short_description = "Export selected to CSV"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv), name='catalogue_product_import_csv'),
        ]
        return custom_urls + urls

    def import_csv(self, request):
        """Import products from CSV"""
        if request.method == 'POST':
            csv_file = request.FILES.get('csv_file')
            if not csv_file:
                messages.error(request, 'Please select a CSV file')
                return redirect('..')

            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'File must be a CSV')
                return redirect('..')

            try:
                # Read CSV file
                decoded_file = csv_file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)

                created_count = 0
                updated_count = 0
                error_count = 0

                for row in reader:
                    try:
                        # Get or create category
                        category_name = row.get('Category', '').strip()
                        if not category_name:
                            error_count += 1
                            continue

                        category, _ = Category.objects.get_or_create(name=category_name)

                        # Check if product exists (by name and category)
                        product_name = row.get('Name', '').strip()
                        if not product_name:
                            error_count += 1
                            continue

                        product, created = Product.objects.update_or_create(
                            name=product_name,
                            category=category,
                            defaults={
                                'description': row.get('Description', ''),
                                'pack_description': row.get('Pack Description', ''),
                                'price_ex_gst': row.get('Price Ex GST') or None,
                                'price_inc_gst': row.get('Price Inc GST') or None,
                                'available': row.get('Available', 'True').lower() in ('true', '1', 'yes'),
                                'stock_quantity': row.get('Stock Quantity') or None,
                            }
                        )

                        # Optionally attach images by filename from the
                        # product_images_import staging folder
                        opened_files = []
                        image_name = row.get('Image', '').strip()
                        if image_name:
                            image_file = get_import_image_file(image_name)
                            if image_file:
                                product.image_main = image_file
                                opened_files.append(image_file)
                            else:
                                messages.warning(
                                    request,
                                    f"'{product_name}': image '{image_name}' not found in product_images_import folder"
                                )

                        alt_image_name = row.get('Alt Image', '').strip()
                        if alt_image_name:
                            alt_image_file = get_import_image_file(alt_image_name)
                            if alt_image_file:
                                product.image_alt = alt_image_file
                                opened_files.append(alt_image_file)
                            else:
                                messages.warning(
                                    request,
                                    f"'{product_name}': alt image '{alt_image_name}' not found in product_images_import folder"
                                )

                        if opened_files:
                            product.save()
                            for f in opened_files:
                                f.close()

                        if created:
                            created_count += 1
                        else:
                            updated_count += 1

                    except Exception as e:
                        error_count += 1
                        continue

                # Show success message
                msg = f'Import completed: {created_count} created, {updated_count} updated'
                if error_count:
                    msg += f', {error_count} errors'
                messages.success(request, msg)

            except Exception as e:
                messages.error(request, f'Error importing CSV: {str(e)}')

            return redirect('..')

        # GET request - show upload form
        context = {
            'title': 'Import Products from CSV',
            'site_title': 'MP Benti Admin',
            'site_header': 'MP Benti Administration',
        }
        return render(request, 'admin/catalogue/product/import_csv.html', context)

    def changelist_view(self, request, extra_context=None):
        """Add import button to changelist"""
        extra_context = extra_context or {}
        extra_context['import_csv_url'] = 'import-csv/'
        return super().changelist_view(request, extra_context=extra_context)
