
from typing import ClassVar

from django.db import models


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        CUSTOMER_DEBT = 'CUSTOMER_DEBT', 'Customer Debt'
        PAYMENT_RECEIVED = 'PAYMENT_RECEIVED', 'Payment Received'
        LOW_STOCK = 'LOW_STOCK', 'Low Stock'
        STOCK_TRANSFER = 'STOCK_TRANSFER', 'Stock Transfer'
        GENERAL = 'GENERAL', 'General'

    recipient = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_sale = models.ForeignKey(
        'sales.Sale',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering: ClassVar[list[str]] = ['-date_created']
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=~models.Q(title=''),
                name='notification_title_not_empty',
            ),
        ]

    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
