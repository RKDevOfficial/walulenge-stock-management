
from decimal import Decimal
from typing import ClassVar

from django.db import models


class CustomerCredit(models.Model):
    customer = models.OneToOneField(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='credit_account',
        limit_choices_to={'role': 'CUSTOMER'}
    )
    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    is_blocked = models.BooleanField(default=False)
    block_reason = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=models.Q(credit_limit__gte=0),
                name='non_negative_customer_credit_limit',
            ),
        ]

    def __str__(self):
        return f"{self.customer.username} - Credit Account"
