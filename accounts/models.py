from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q


class User(AbstractUser):
    class Role(models.TextChoices):
        MANAGER = 'MANAGER', 'Manager'
        SHOPKEEPER = 'SHOPKEEPER', 'Shopkeeper'
        MECHANIC = 'MECHANIC', 'Mechanic'
        CUSTOMER = 'CUSTOMER', 'Customer'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    profile_picture = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True,
    )

    def get_role_display(self) -> str:
        """Return the human-readable label for this user's role."""
        for value, label in self.Role.choices:
            if value == self.role:
                return str(label)
        return str(self.role)

    def __str__(self) -> str:
        return f"{self.username} - {self.get_role_display()}"

class UserShop(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shop_assignments'
    )
    shop = models.ForeignKey(
        'inventory.Shop',
        on_delete=models.PROTECT,
        related_name='staff_members'
    )
    date_assigned = models.DateTimeField(auto_now_add=True)
    date_ended = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=['user', 'shop'],
                condition=Q(is_active=True),
                name='unique_active_user_shop',
            ),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.shop.name}"
