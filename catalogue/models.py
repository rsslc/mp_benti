from django.db import models
from django.utils.text import slugify
from .utils import process_category_image, process_product_image


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name_plural = "categories"
        ordering = ['name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        # Process image if it's being uploaded/changed
        if self.image and hasattr(self.image, 'file'):
            try:
                processed_image = process_category_image(self.image)
                if processed_image:
                    self.image = processed_image
            except Exception:
                # If processing fails, keep the original image
                pass

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        if self.parent:
            return reverse('category_detail', kwargs={'parent_slug': self.parent.slug, 'child_slug': self.slug})
        return reverse('parent_category_detail', kwargs={'category_slug': self.slug})

    @property
    def is_parent(self):
        return self.parent is None

    @property
    def is_child(self):
        return self.parent is not None

    def get_all_products(self):
        """Get products from this category and all its children"""
        if self.is_parent:
            # For parent categories, get products from all children
            products = Product.objects.none()
            for child in self.children.all():
                products = products | child.products.all()
            # Also include products directly in parent category (backward compatibility)
            products = products | self.products.all()
            return products
        else:
            # For child categories, return own products
            return self.products.all()


class Product(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=50, blank=True)
    unit_weight = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    pack_size = models.CharField(max_length=100, blank=True)
    price_ex_gst = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    price_inc_gst = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    available = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(null=True, blank=True)
    image_main = models.ImageField(upload_to="products/", blank=True, null=True)
    image_alt = models.ImageField(upload_to="products/", blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Process main image if it's being uploaded/changed
        if self.image_main and hasattr(self.image_main, 'file'):
            try:
                processed_image = process_product_image(self.image_main)
                if processed_image:
                    self.image_main = processed_image
            except Exception:
                # If processing fails, keep the original image
                pass

        # Process alt image if it's being uploaded/changed
        if self.image_alt and hasattr(self.image_alt, 'file'):
            try:
                processed_image = process_product_image(self.image_alt)
                if processed_image:
                    self.image_alt = processed_image
            except Exception:
                # If processing fails, keep the original image
                pass

        super().save(*args, **kwargs)
