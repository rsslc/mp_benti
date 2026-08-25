from django.db import migrations


def delete_alt_image_files(apps, schema_editor):
    Product = apps.get_model('catalogue', 'Product')
    for product in Product.objects.exclude(image_alt='').exclude(image_alt__isnull=True):
        product.image_alt.delete(save=False)


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0010_alter_product_options'),
    ]

    operations = [
        migrations.RunPython(delete_alt_image_files, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='product',
            name='image_alt',
        ),
    ]
