# Generated for Lumiere account engagement records.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('products', '0002_product_brightness_product_color_family_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='UrlAnalysisRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_url', models.URLField(max_length=1000)),
                ('title', models.CharField(blank=True, max_length=300)),
                ('brand', models.CharField(blank=True, max_length=120)),
                ('product_name', models.CharField(blank=True, max_length=300)),
                ('image_url', models.URLField(blank=True, max_length=1000)),
                ('colors', models.JSONField(blank=True, default=list)),
                ('result_payload', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='url_analysis_records',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='LikedProductOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('option_id', models.CharField(blank=True, max_length=120)),
                ('group_key', models.CharField(blank=True, db_index=True, max_length=200)),
                ('brand', models.CharField(blank=True, max_length=120)),
                ('name', models.CharField(blank=True, max_length=300)),
                ('option', models.CharField(blank=True, max_length=200)),
                ('image_url', models.URLField(blank=True, max_length=1000)),
                ('product_url', models.URLField(blank=True, max_length=1000)),
                ('snapshot', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'product',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='liked_by_users',
                        to='products.product',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='liked_product_options',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='likedproductoption',
            constraint=models.UniqueConstraint(
                fields=('user', 'product', 'option_id'),
                name='unique_liked_product_option',
            ),
        ),
    ]
