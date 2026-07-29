from django.db import migrations, models


def populate_pack_description(apps, schema_editor):
    Product = apps.get_model('catalogue', 'Product')
    for product in Product.objects.all():
        pack_size = (product.pack_size or '').strip()
        if pack_size:
            description = pack_size
        else:
            parts = []
            if product.unit_weight:
                parts.append(str(product.unit_weight))
            if product.unit:
                parts.append(product.unit)
            description = ' '.join(parts).strip()
        product.pack_description = description
        product.save(update_fields=['pack_description'])


def reverse_pack_description(apps, schema_editor):
    Product = apps.get_model('catalogue', 'Product')
    for product in Product.objects.all():
        product.pack_size = product.pack_description
        product.save(update_fields=['pack_size'])


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0007_load_initial_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='pack_description',
            field=models.CharField(max_length=150, blank=True, default=''),
        ),
        migrations.RunPython(populate_pack_description, reverse_pack_description),
        migrations.RemoveField(
            model_name='product',
            name='unit',
        ),
        migrations.RemoveField(
            model_name='product',
            name='unit_weight',
        ),
        migrations.RemoveField(
            model_name='product',
            name='pack_size',
        ),
    ]
