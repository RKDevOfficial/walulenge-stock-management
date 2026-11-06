# Generated for employee shop assignment history.

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserShop',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_assigned', models.DateTimeField(auto_now_add=True)),
                ('date_ended', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='staff_members', to='inventory.shop')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shop_assignments', to='accounts.user')),
            ],
        ),
        migrations.AddConstraint(
            model_name='usershop',
            constraint=models.UniqueConstraint(condition=Q(('is_active', True)), fields=('user',), name='unique_active_shop_per_user'),
        ),
    ]
