# Generated for the initial inventory shop model.

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Shop',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True)),
                ('location', models.CharField(blank=True, max_length=255)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
