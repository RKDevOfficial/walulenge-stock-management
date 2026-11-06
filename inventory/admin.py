from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import (
    Shop,
    Stock,
    StockTransaction,
    StockTransfer,
    StockTransferItem,
)
from .services import record_stock_transaction, reverse_stock_transaction


@admin.action(description="Reverse selected stock transactions")
def reverse_transactions(modeladmin, request, queryset):
    if request.user.role != 'MANAGER':
        messages.error(request, "Only managers can reverse stock transactions.")
        return

    reversed_count = 0
    for original in queryset:
        try:
            reverse_stock_transaction(
                original,
                request.user,
                notes=f"Reversed by {request.user.username} through Admin.",
            )
            reversed_count += 1
        except ValidationError as error:
            messages.error(
                request,
                f"Transaction {original.pk}: {error}",
            )

    if reversed_count:
        messages.success(
            request,
            f"Successfully reversed {reversed_count} transaction(s).",
        )


admin.site.register(Shop)
admin.site.register(Stock)
admin.site.register(StockTransfer)
admin.site.register(StockTransferItem)


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'reference',
        'stock',
        'transaction_type',
        'direction',
        'quantity',
        'unit_cost',
        'performed_by',
        'transaction_date',
    )
    list_filter = (
        'transaction_type',
        'direction',
        'transaction_date',
    )
    actions = [reverse_transactions]

    def get_actions(self, request):
        actions = super().get_actions(request)
        if request.user.role != 'MANAGER':
            actions.pop('reverse_transactions', None)
        return actions

    def has_change_permission(self, request, obj=None):
        if obj is not None:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if change:
            raise ValidationError(
                "Existing stock transactions cannot be edited."
            )
        record_stock_transaction(obj)
