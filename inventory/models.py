from decimal import Decimal
from typing import ClassVar

from django.db import models


class Shop(models.Model):
    name = models.CharField(max_length=150, unique=True)
    location = models.CharField(max_length=255, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Stock(models.Model):
    shop = models.ForeignKey(
        Shop,
        on_delete=models.PROTECT,
        related_name='stock_records'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='shop_stock'
    )
    quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=5)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=['shop', 'product'],
                name='unique_product_stock_per_shop'
            )
        ]

    def __str__(self):
        return f"{self.product.name} - {self.shop.name}: {self.quantity}"


class StockTransaction(models.Model):
    class TransactionType(models.TextChoices):
        PURCHASE = 'PURCHASE', 'Purchase'
        SALE = 'SALE', 'Sale'
        RETURN = 'RETURN', 'Return'
        ADJUSTMENT = 'ADJUSTMENT', 'Adjustment'
        DAMAGE = 'DAMAGE', 'Damaged Stock'
        TRANSFER_IN = 'TRANSFER_IN', 'Transfer In'
        TRANSFER_OUT = 'TRANSFER_OUT', 'Transfer Out'

    class Direction(models.TextChoices):
        IN = 'IN', 'Stock In'
        OUT = 'OUT', 'Stock Out'

    stock = models.ForeignKey(
        Stock,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    reversal_of = models.OneToOneField(
        'self',
        on_delete=models.PROTECT,
        related_name='reversal',
        null=True,
        blank=True,
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices
    )
    direction = models.CharField(
        max_length=3,
        choices=Direction.choices
    )
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='stock_transactions'
    )
    transaction_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name='positive_stock_transaction_quantity',
            ),
        ]

    def __str__(self):
        return f"{self.transaction_type} - {self.stock.product.name} ({self.quantity})"

class StockTransfer(models.Model):
    class TransferStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SENT = 'SENT', 'Sent'
        RECEIVED = 'RECEIVED', 'Received'
        CANCELLED = 'CANCELLED', 'Cancelled'

    source_shop = models.ForeignKey(
        Shop,
        on_delete=models.PROTECT,
        related_name='outgoing_transfers'
    )
    destination_shop = models.ForeignKey(
        Shop,
        on_delete=models.PROTECT,
        related_name='incoming_transfers'
    )
    status = models.CharField(
        max_length=20,
        choices=TransferStatus.choices,
        default=TransferStatus.DRAFT
    )
    initiated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='initiated_transfers'
    )
    notes = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_sent = models.DateTimeField(null=True, blank=True)
    date_received = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=~models.Q(source_shop=models.F('destination_shop')),
                name='different_transfer_shops',
            ),
        ]

    def __str__(self):
        return f"{self.source_shop} to {self.destination_shop}"


class StockTransferItem(models.Model):
    transfer = models.ForeignKey(
        StockTransfer,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='transfer_items'
    )
    quantity = models.PositiveIntegerField()

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=['transfer', 'product'],
                name='unique_product_per_transfer',
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name='positive_transfer_item_quantity',
            ),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"

