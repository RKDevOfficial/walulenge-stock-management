# Generated for shop stock tracking.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=0)),
                ('reorder_level', models.PositiveIntegerField(default=5)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='shop_stock', to='products.product')),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='stock_records', to='inventory.shop')),
            ],
        ),
        migrations.AddConstraint(
            model_name='stock',
            constraint=models.UniqueConstraint(fields=('shop', 'product'), name='unique_product_stock_per_shop'),
        ),
    ]
