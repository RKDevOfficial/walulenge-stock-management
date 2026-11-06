from decimal import Decimal
from typing import ClassVar

from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )
    suppliers = models.ManyToManyField(
        Supplier,
        through='ProductSupplier',
        related_name='products'
    )
    name = models.CharField(max_length=200)
    product_code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    buying_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    retail_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    wholesale_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
    )
    is_available = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.product_code})"

class ProductSupplier(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='supplier_links'
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='product_links'
    )
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=['product', 'supplier'],
                name='unique_product_supplier'
            )
        ]

    def __str__(self):
        return f"{self.product.name} - {self.supplier.name}"
