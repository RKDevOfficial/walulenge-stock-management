from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.core.exceptions import ValidationError

from accounts.models import User, UserShop
from products.models import Product
from .models import (
    Stock,
    Shop,
    StockTransaction,
    StockTransfer,
    StockTransferItem,
)
from .services import (
    record_stock_transaction,
    send_stock_transfer,
    receive_stock_transfer,
    cancel_stock_transfer,
)


@login_required
def stock_list(request):
    if request.user.role == User.Role.MANAGER:
        shops = Shop.objects.all().order_by('name')
    elif request.user.role == User.Role.SHOPKEEPER:
        assigned_shop_ids = UserShop.objects.filter(
            user=request.user,
            is_active=True,
        ).values_list('shop_id', flat=True)
        shops = Shop.objects.filter(
            pk__in=assigned_shop_ids
        ).distinct().order_by('name')
    else:
        return redirect('dashboard')

    search_query = request.GET.get('search', '').strip()
    selected_shop = request.GET.get('shop', '').strip()
    stocks = Stock.objects.select_related(
        'shop', 'product', 'product__category'
    ).filter(
        shop__in=shops
    ).order_by('shop__name', 'product__name')

    if selected_shop.isdigit() and shops.filter(pk=selected_shop).exists():
        stocks = stocks.filter(shop_id=selected_shop)
    else:
        selected_shop = ''

    if search_query:
        stocks = stocks.filter(
            Q(product__name__icontains=search_query)
            | Q(product__product_code__icontains=search_query)
            | Q(product__category__name__icontains=search_query)
        )

    total_stock_records = stocks.count()
    low_stock_count = stocks.filter(
        quantity__gt=0,
        quantity__lte=F('reorder_level'),
    ).count()
    out_of_stock_count = stocks.filter(quantity=0).count()

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'low':
        stocks = stocks.filter(
            quantity__gt=0,
            quantity__lte=F('reorder_level'),
        )
    elif status_filter == 'out':
        stocks = stocks.filter(quantity=0)
    elif status_filter == 'available':
        stocks = stocks.filter(quantity__gt=F('reorder_level'))
    else:
        status_filter = ''

    paginator = Paginator(stocks, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'shops': shops,
        'stocks': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_shop': selected_shop,
        'selected_status': status_filter,
        'total_stock_records': total_stock_records,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
    }
    return render(request, 'inventory/stock_list.html', context)


@login_required
def stock_add(request):
    if request.user.role not in [User.Role.MANAGER, User.Role.SHOPKEEPER]:
        return redirect('dashboard')

    if request.user.role == User.Role.MANAGER:
        shops = Shop.objects.all()
    else:
        shops = Shop.objects.filter(
            staff_members__user=request.user,
            staff_members__is_active=True
        ).distinct()

    if request.method == 'POST':
        try:
            stock = get_object_or_404(
                Stock,
                pk=request.POST.get('stock'),
                shop__in=shops,
            )
            transaction_type = request.POST.get('transaction_type')
            quantity = int(request.POST.get('quantity'))
            unit_cost = request.POST.get('unit_cost') or '0.00'

            if transaction_type not in [
                StockTransaction.TransactionType.PURCHASE,
                StockTransaction.TransactionType.RETURN,
                StockTransaction.TransactionType.ADJUSTMENT,
            ]:
                raise ValidationError('Invalid stock-in transaction type.')

            stock_transaction = StockTransaction(
                stock=stock,
                transaction_type=transaction_type,
                direction=StockTransaction.Direction.IN,
                quantity=quantity,
                unit_cost=unit_cost,
                reference=request.POST.get('reference', '').strip(),
                notes=request.POST.get('notes', '').strip(),
                performed_by=request.user,
            )
            record_stock_transaction(stock_transaction)
            messages.success(request, 'Stock added successfully.')
            return redirect('stock_list')
        except (ValidationError, ValueError, TypeError) as error:
            messages.error(request, str(error))

    context = {
        'stocks': Stock.objects.filter(shop__in=shops).select_related(
            'shop', 'product'
        ),
        'transaction_types': [
            StockTransaction.TransactionType.PURCHASE,
            StockTransaction.TransactionType.RETURN,
            StockTransaction.TransactionType.ADJUSTMENT,
        ],
    }
    return render(request, 'inventory/stock_add.html', context)


@login_required
def stock_remove(request):
    if request.user.role not in [User.Role.MANAGER, User.Role.SHOPKEEPER]:
        return redirect('dashboard')

    if request.user.role == User.Role.MANAGER:
        shops = Shop.objects.all()
    else:
        shops = Shop.objects.filter(
            staff_members__user=request.user,
            staff_members__is_active=True,
        ).distinct()

    if request.method == 'POST':
        try:
            stock = get_object_or_404(
                Stock,
                pk=request.POST.get('stock'),
                shop__in=shops,
            )
            transaction_type = request.POST.get('transaction_type')
            quantity = int(request.POST.get('quantity'))
            unit_cost = request.POST.get('unit_cost') or '0.00'
            notes = request.POST.get('notes', '').strip()

            if transaction_type not in [
                StockTransaction.TransactionType.DAMAGE,
                StockTransaction.TransactionType.ADJUSTMENT,
            ]:
                raise ValidationError('Invalid stock-out transaction type.')
            if not notes:
                raise ValidationError('A reason is required for stock removal.')

            stock_transaction = StockTransaction(
                stock=stock,
                transaction_type=transaction_type,
                direction=StockTransaction.Direction.OUT,
                quantity=quantity,
                unit_cost=unit_cost,
                reference=request.POST.get('reference', '').strip(),
                notes=notes,
                performed_by=request.user,
            )
            record_stock_transaction(stock_transaction)
            messages.success(request, 'Stock removed successfully.')
            return redirect('stock_list')
        except (ValidationError, ValueError, TypeError) as error:
            messages.error(request, str(error))

    context = {
        'stocks': Stock.objects.filter(shop__in=shops).select_related(
            'shop', 'product'
        ),
    }
    return render(request, 'inventory/stock_remove.html', context)


@login_required
def stock_transactions(request):
    if request.user.role == User.Role.MANAGER:
        shops = Shop.objects.all()
    elif request.user.role == User.Role.SHOPKEEPER:
        assigned_shop_ids = UserShop.objects.filter(
            user=request.user,
            is_active=True,
        ).values_list('shop_id', flat=True)
        shops = Shop.objects.filter(pk__in=assigned_shop_ids).distinct()
    else:
        return redirect('dashboard')

    transactions = StockTransaction.objects.select_related(
        'stock__shop', 'stock__product', 'performed_by'
    ).filter(
        stock__shop__in=shops
    ).order_by('-transaction_date')
    search_query = request.GET.get('search', '').strip()
    if search_query:
        transactions = transactions.filter(
            Q(stock__product__name__icontains=search_query)
            | Q(stock__product__product_code__icontains=search_query)
            | Q(reference__icontains=search_query)
            | Q(performed_by__username__icontains=search_query)
        )

    return render(request, 'inventory/stock_transactions.html', {
        'transactions': transactions,
        'search_query': search_query,
        'total_transactions': transactions.count(),
        'shops': shops,
    })


@login_required
def stock_transfer_list(request):
    if request.user.role != User.Role.MANAGER:
        return redirect('dashboard')

    transfers = StockTransfer.objects.select_related(
        'source_shop',
        'destination_shop',
        'initiated_by',
    ).prefetch_related(
        'items__product'
    ).order_by('-date_created')
    status = request.GET.get('status', '').strip()
    search_query = request.GET.get('search', '').strip()
    if status in StockTransfer.TransferStatus.values:
        transfers = transfers.filter(status=status)
    else:
        status = ''
    if search_query:
        transfers = transfers.filter(
            Q(source_shop__name__icontains=search_query)
            | Q(destination_shop__name__icontains=search_query)
            | Q(initiated_by__username__icontains=search_query)
        ).distinct()

    return render(request, 'inventory/stock_transfer_list.html', {
        'transfers': transfers,
        'search_query': search_query,
        'selected_status': status,
        'statuses': StockTransfer.TransferStatus.choices,
    })


@login_required
def stock_transfer_create(request):
    if request.user.role != User.Role.MANAGER:
        return redirect('dashboard')

    shops = Shop.objects.order_by('name')
    products = Product.objects.order_by('name')
    if request.method == 'POST':
        try:
            source_shop = get_object_or_404(
                Shop, pk=request.POST.get('source_shop')
            )
            destination_shop = get_object_or_404(
                Shop, pk=request.POST.get('destination_shop')
            )
            if source_shop.pk == destination_shop.pk:
                raise ValidationError('Choose two different shops.')

            product_ids = request.POST.getlist('product_ids')
            quantities = request.POST.getlist('quantities')
            if not product_ids or len(product_ids) != len(quantities):
                raise ValidationError(
                    'Add at least one product and provide a quantity for each.'
                )
            if len(product_ids) != len(set(product_ids)):
                raise ValidationError(
                    'Each product can only be added once to a transfer.'
                )

            parsed_items = []
            for product_id, raw_quantity in zip(product_ids, quantities):
                quantity = int(raw_quantity)
                if quantity <= 0:
                    raise ValidationError('Quantities must be greater than zero.')
                product = get_object_or_404(Product, pk=product_id)
                parsed_items.append((product, quantity))

            with transaction.atomic():
                transfer = StockTransfer.objects.create(
                    source_shop=source_shop,
                    destination_shop=destination_shop,
                    initiated_by=request.user,
                    notes=request.POST.get('notes', '').strip(),
                )
                StockTransferItem.objects.bulk_create([
                    StockTransferItem(
                        transfer=transfer,
                        product=product,
                        quantity=quantity,
                    )
                    for product, quantity in parsed_items
                ])

            messages.success(request, 'Draft stock transfer created.')
            return redirect('stock_transfer_detail', pk=transfer.pk)
        except (ValidationError, ValueError, TypeError) as error:
            messages.error(request, '; '.join(error.messages) if isinstance(error, ValidationError) else str(error))

    return render(request, 'inventory/stock_transfer_form.html', {
        'shops': shops,
        'products': products,
    })


@login_required
def stock_transfer_detail(request, pk):
    if request.user.role != User.Role.MANAGER:
        return redirect('dashboard')

    transfer = get_object_or_404(
        StockTransfer.objects.select_related(
            'source_shop', 'destination_shop', 'initiated_by'
        ).prefetch_related('items__product'),
        pk=pk,
    )
    return render(request, 'inventory/stock_transfer_detail.html', {
        'transfer': transfer,
        'items': transfer.items.select_related('product'),
    })


@login_required
@require_POST
def stock_transfer_send(request, pk):
    if request.user.role != User.Role.MANAGER:
        return redirect('dashboard')

    transfer = get_object_or_404(StockTransfer, pk=pk)
    try:
        send_stock_transfer(transfer, request.user)
        messages.success(request, 'Stock transfer sent successfully.')
    except ValidationError as error:
        messages.error(request, '; '.join(error.messages))
    return redirect('stock_transfer_detail', pk=pk)


@login_required
@require_POST
def stock_transfer_receive(request, pk):
    if request.user.role != User.Role.MANAGER:
        return redirect('dashboard')

    transfer = get_object_or_404(StockTransfer, pk=pk)
    try:
        receive_stock_transfer(transfer, request.user)
        messages.success(request, 'Stock transfer received successfully.')
    except ValidationError as error:
        messages.error(request, '; '.join(error.messages))
    return redirect('stock_transfer_detail', pk=pk)


@login_required
@require_POST
def stock_transfer_cancel(request, pk):
    if request.user.role != User.Role.MANAGER:
        return redirect('dashboard')

    transfer = get_object_or_404(StockTransfer, pk=pk)
    try:
        cancel_stock_transfer(transfer, request.user)
        messages.success(request, 'Stock transfer cancelled.')
    except ValidationError as error:
        messages.error(request, '; '.join(error.messages))
    return redirect('stock_transfer_detail', pk=pk)
