from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Stock, StockTransaction, StockTransfer


@transaction.atomic
def record_stock_transaction(stock_transaction):
    if not stock_transaction._state.adding:
        raise ValidationError(
            "Only new stock transactions can be recorded through this service."
        )

    stock = Stock.objects.select_for_update().get(
        pk=stock_transaction.stock_id
    )

    if stock_transaction.quantity <= 0:
        raise ValidationError("Transaction quantity must be greater than zero.")

    if stock_transaction.direction == StockTransaction.Direction.IN:
        stock.quantity += stock_transaction.quantity
    elif stock_transaction.direction == StockTransaction.Direction.OUT:
        if stock_transaction.quantity > stock.quantity:
            raise ValidationError("Insufficient stock for this transaction.")
        stock.quantity -= stock_transaction.quantity
    else:
        raise ValidationError("Invalid stock transaction direction.")

    stock.save(update_fields=["quantity", "last_updated"])
    stock_transaction.save()


@transaction.atomic
def reverse_stock_transaction(stock_transaction, performed_by, notes=None):
    if stock_transaction._state.adding or stock_transaction.pk is None:
        raise ValidationError("Only saved stock transactions can be reversed.")

    original = StockTransaction.objects.select_for_update().get(
        pk=stock_transaction.pk
    )
    if StockTransaction.objects.filter(reversal_of=original).exists():
        raise ValidationError("This stock transaction has already been reversed.")
    if original.reversal_of_id is not None:
        raise ValidationError(
            "A reversal transaction cannot itself be reversed."
        )

    if original.direction == StockTransaction.Direction.IN:
        reversal_direction = StockTransaction.Direction.OUT
    elif original.direction == StockTransaction.Direction.OUT:
        reversal_direction = StockTransaction.Direction.IN
    else:
        raise ValidationError("Invalid stock transaction direction.")

    reversal = StockTransaction(
        stock=original.stock,
        reversal_of=original,
        transaction_type=StockTransaction.TransactionType.ADJUSTMENT,
        direction=reversal_direction,
        quantity=original.quantity,
        unit_cost=original.unit_cost,
        reference=f"Reversal of transaction {original.pk}",
        notes=notes or f"Reversal of transaction {original.pk}.",
        performed_by=performed_by,
    )
    record_stock_transaction(reversal)
    return reversal


@transaction.atomic
def send_stock_transfer(transfer, performed_by):
    transfer = StockTransfer.objects.select_for_update().get(pk=transfer.pk)
    if transfer.status != StockTransfer.TransferStatus.DRAFT:
        raise ValidationError("Only draft transfers can be sent.")

    items = list(transfer.items.select_related('product').order_by('product_id'))
    if not items:
        raise ValidationError("Add at least one product before sending.")

    product_ids = [item.product_id for item in items]
    source_stocks = Stock.objects.select_for_update().filter(
        shop=transfer.source_shop,
        product_id__in=product_ids,
    ).order_by('product_id')
    stock_map = {stock.product_id: stock for stock in source_stocks}

    for item in items:
        stock = stock_map.get(item.product_id)
        if stock is None:
            raise ValidationError(
                f"{item.product.name} has no stock record "
                f"in {transfer.source_shop.name}."
            )
        if item.quantity > stock.quantity:
            raise ValidationError(
                f"Insufficient stock for {item.product.name} "
                f"in {transfer.source_shop.name}."
            )

    for item in items:
        stock = stock_map[item.product_id]
        stock_transaction = StockTransaction(
            stock=stock,
            transaction_type=StockTransaction.TransactionType.TRANSFER_OUT,
            direction=StockTransaction.Direction.OUT,
            quantity=item.quantity,
            reference=f"Transfer {transfer.pk}",
            notes=f"Sent to {transfer.destination_shop.name}.",
            performed_by=performed_by,
        )
        record_stock_transaction(stock_transaction)

    transfer.status = StockTransfer.TransferStatus.SENT
    transfer.date_sent = timezone.now()
    transfer.save(update_fields=['status', 'date_sent'])
    return transfer


@transaction.atomic
def receive_stock_transfer(transfer, performed_by):
    transfer = StockTransfer.objects.select_for_update().get(pk=transfer.pk)
    if transfer.status != StockTransfer.TransferStatus.SENT:
        raise ValidationError("Only sent transfers can be received.")

    items = list(transfer.items.select_related('product').order_by('product_id'))
    if not items:
        raise ValidationError("This transfer has no items to receive.")

    for item in items:
        stock, _ = Stock.objects.get_or_create(
            shop=transfer.destination_shop,
            product=item.product,
            defaults={'quantity': 0},
        )
        stock = Stock.objects.select_for_update().get(pk=stock.pk)
        stock_transaction = StockTransaction(
            stock=stock,
            transaction_type=StockTransaction.TransactionType.TRANSFER_IN,
            direction=StockTransaction.Direction.IN,
            quantity=item.quantity,
            reference=f"Transfer {transfer.pk}",
            notes=f"Received from {transfer.source_shop.name}.",
            performed_by=performed_by,
        )
        record_stock_transaction(stock_transaction)

    transfer.status = StockTransfer.TransferStatus.RECEIVED
    transfer.date_received = timezone.now()
    transfer.save(update_fields=['status', 'date_received'])
    return transfer


@transaction.atomic
def cancel_stock_transfer(transfer, performed_by):
    transfer = StockTransfer.objects.select_for_update().get(pk=transfer.pk)
    if transfer.status == StockTransfer.TransferStatus.RECEIVED:
        raise ValidationError(
            "Received transfers cannot be cancelled because stock may have been sold."
        )
    if transfer.status == StockTransfer.TransferStatus.CANCELLED:
        raise ValidationError("This transfer has already been cancelled.")

    if transfer.status == StockTransfer.TransferStatus.SENT:
        outgoing_transactions = list(
            StockTransaction.objects.select_for_update().filter(
                stock__shop=transfer.source_shop,
                transaction_type=StockTransaction.TransactionType.TRANSFER_OUT,
                reference=f"Transfer {transfer.pk}",
            ).order_by('pk')
        )
        if len(outgoing_transactions) != transfer.items.count():
            raise ValidationError(
                "Transfer stock movements are incomplete; this transfer cannot be cancelled safely."
            )
        for stock_transaction in outgoing_transactions:
            reverse_stock_transaction(
                stock_transaction,
                performed_by,
                notes=f"Cancelled transfer {transfer.pk}; source stock restored.",
            )
    elif transfer.status != StockTransfer.TransferStatus.DRAFT:
        raise ValidationError("This transfer cannot be cancelled in its current status.")

    transfer.status = StockTransfer.TransferStatus.CANCELLED
    transfer.save(update_fields=['status'])
    return transfer
