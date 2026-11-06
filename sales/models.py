
from decimal import Decimal
from typing import ClassVar

from django.db import models


class Sale(models.Model):
    class SaleType(models.TextChoices):
        RETAIL = 'RETAIL', 'Retail'
        WHOLESALE = 'WHOLESALE', 'Wholesale'

    class PaymentStatus(models.TextChoices):
        PAID = 'PAID', 'Paid'
        PARTIAL = 'PARTIAL', 'Partially Paid'
        CREDIT = 'CREDIT', 'Credit'

    class PaymentPlan(models.TextChoices):
        CASH = 'CASH', 'Cash'
        CREDIT = 'CREDIT', 'Credit'
        INSTALLMENT = 'INSTALLMENT', 'Installment'

    shop = models.ForeignKey(
        'inventory.Shop',
        on_delete=models.PROTECT,
        related_name='sales'
    )
    customer = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='customer_sales',
        null=True,
        blank=True
    )
    sale_type = models.CharField(
        max_length=20,
        choices=SaleType.choices
    )
    cashier = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='processed_sales'
    )
    receipt_number = models.CharField(
        max_length=50,
        unique=True
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PAID
    )
    payment_plan = models.CharField(
        max_length=20,
        choices=PaymentPlan.choices,
        default=PaymentPlan.CASH
    )
    goods_released = models.BooleanField(default=False)
    release_date = models.DateTimeField(null=True, blank=True)
    released_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='released_sales',
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True)
    sale_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.receipt_number


class SaleItem(models.Model):
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='sale_items'
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"


    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name='positive_sale_item_quantity'
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0),
                name='non_negative_sale_item_price'
            ),
            models.CheckConstraint(
                condition=models.Q(discount_amount__gte=0),
                name='non_negative_sale_item_discount'
            ),
            models.CheckConstraint(
                condition=models.Q(subtotal__gte=0),
                name='non_negative_sale_item_subtotal'
            ),
            models.CheckConstraint(
                condition=models.Q(total_amount__gte=0),
                name='non_negative_sale_item_total'
            ),
        ]


class SalePayment(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        MOBILE_MONEY = 'MOBILE_MONEY', 'Mobile Money'
        BANK = 'BANK', 'Bank Transfer'
        OTHER = 'OTHER', 'Other'

    sale = models.ForeignKey(
        Sale,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH
    )
    reference = models.CharField(
        max_length=100,
        blank=True
    )
    received_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='received_payments'
    )
    notes = models.TextField(blank=True)
    payment_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name='positive_sale_payment_amount'
            )
        ]

    def __str__(self):
        return f"{self.sale.receipt_number} - {self.amount}"


class BicycleFrameSale(models.Model):
    class ItemType(models.TextChoices):
        BICYCLE = 'BICYCLE', 'Bicycle'
        FRAME = 'FRAME', 'Frame'

    shop = models.ForeignKey(
        'inventory.Shop',
        on_delete=models.PROTECT,
        related_name='bicycle_frame_sales'
    )
    customer = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='bicycle_frame_purchases',
        null=True,
        blank=True
    )
    receipt_number = models.CharField(
        max_length=50,
        unique=True
    )
    manufacturer_item_number = models.CharField(
        max_length=50,
        unique=True
    )
    item_type = models.CharField(
        max_length=20,
        choices=ItemType.choices
    )
    brand = models.CharField(max_length=100)
    supplier = models.ForeignKey(
        'products.Supplier',
        on_delete=models.PROTECT,
        related_name='bicycle_frame_sales'
    )
    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    is_taken = models.BooleanField(default=False)
    date_taken = models.DateTimeField(null=True, blank=True)
    sold_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='processed_bicycle_frame_sales'
    )
    sale_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=models.Q(selling_price__gte=0),
                name='non_negative_bicycle_frame_price',
            ),
        ]

    def __str__(self):
        return self.receipt_number


class BicycleFramePayment(models.Model):
    bicycle_frame_sale = models.ForeignKey(
        BicycleFrameSale,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    received_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='received_bicycle_frame_payments'
    )
    reference = models.CharField(
        max_length=100,
        blank=True
    )
    notes = models.TextField(blank=True)
    payment_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name='positive_bicycle_frame_payment'
            )
        ]

    def __str__(self):
        return f"{self.bicycle_frame_sale.receipt_number} - {self.amount}"
