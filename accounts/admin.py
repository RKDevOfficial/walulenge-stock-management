from typing import Any, cast

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, UserShop


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
        'role',
        'phone_number',
        'is_active',
    )

    list_filter = ('role', 'is_active', 'is_staff')

    search_fields = (
        'username',
        'first_name',
        'last_name',
        'email',
        'phone_number',
    )

    fieldsets = cast(Any, UserAdmin.fieldsets) + (
        ('Additional Information', {
            'fields': ('role', 'phone_number', 'profile_picture'),
        }),
    )

    add_fieldsets = cast(Any, UserAdmin.add_fieldsets) + (
        ('Additional Information', {
            'fields': ('role', 'phone_number', 'profile_picture'),
        }),
    )


@admin.register(UserShop)
class UserShopAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'shop',
        'is_active',
        'date_assigned',
        'date_ended',
    )

    list_filter = ('shop', 'is_active')

    search_fields = (
        'user__username',
        'shop__name',
    )
