from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db.models import Sum, F, Value, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone

from products.models import Product
from inventory.models import Shop, Stock, StockTransaction
from sales.models import (
    Sale,
    SalePayment,
    BicycleFrameSale,
    BicycleFramePayment,
)
from customers.models import CustomerCredit

from .models import User


def user_login(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')

    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def dashboard(request):

    role = request.user.role

    if role == User.Role.MANAGER:
        return redirect('manager_dashboard')

    elif role == User.Role.SHOPKEEPER:
        return redirect('shopkeeper_dashboard')

    elif role == User.Role.MECHANIC:
        return redirect('mechanic_dashboard')

    elif role == User.Role.CUSTOMER:
        return redirect('customer_dashboard')

    return redirect('login')


@login_required
def manager_dashboard(request):
    if request.user.role != User.Role.MANAGER:
        return redirect('dashboard')

    today = timezone.localdate()
    money_field = DecimalField(max_digits=14, decimal_places=2)
    zero_money = Value(Decimal('0.00'), output_field=money_field)

    total_products = Product.objects.count()
    available_products = Product.objects.filter(
        is_available=True
    ).count()
    total_stock_units = Stock.objects.aggregate(
        total=Sum('quantity')
    )['total'] or 0
    low_stock_count = Stock.objects.filter(
        quantity__lte=F('reorder_level')
    ).count()

    today_sales = Sale.objects.filter(
        sale_date__date=today
    ).aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')
    today_frame_sales = BicycleFrameSale.objects.filter(
        sale_date__date=today
    ).aggregate(
        total=Sum('selling_price')
    )['total'] or Decimal('0.00')

    today_sale_payments = SalePayment.objects.filter(
        payment_date__date=today
    ).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    today_frame_payments = BicycleFramePayment.objects.filter(
        payment_date__date=today
    ).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')

    ordinary_debt = Sale.objects.aggregate(
        total=Coalesce(Sum('balance'), zero_money)
    )['total']
    frame_debt = BicycleFrameSale.objects.annotate(
        amount_paid=Coalesce(Sum('payments__amount'), zero_money)
    ).aggregate(
        total=Coalesce(
            Sum(F('selling_price') - F('amount_paid')),
            zero_money,
        )
    )['total']
    blocked_customers = CustomerCredit.objects.filter(
        is_blocked=True
    ).count()

    recent_sales = Sale.objects.select_related(
        'shop', 'customer', 'cashier'
    ).order_by('-sale_date')[:5]
    recent_transactions = StockTransaction.objects.select_related(
        'stock__shop',
        'stock__product',
        'performed_by'
    ).order_by('-transaction_date')[:5]

    context = {
        'total_products': total_products,
        'available_products': available_products,
        'total_stock_units': total_stock_units,
        'low_stock_count': low_stock_count,
        'today_sales': today_sales + today_frame_sales,
        'today_collections': today_sale_payments + today_frame_payments,
        'total_debt': ordinary_debt + frame_debt,
        'blocked_customers': blocked_customers,
        'recent_sales': recent_sales,
        'recent_transactions': recent_transactions,
    }
    return render(
        request,
        'accounts/manager_dashboard.html',
        context
    )

@login_required
def shopkeeper_dashboard(request):
    if request.user.role != User.Role.SHOPKEEPER:
        return redirect('dashboard')

    return render(request, 'accounts/shopkeeper_dashboard.html')


@login_required
def mechanic_dashboard(request):
    if request.user.role != User.Role.MECHANIC:
        return redirect('dashboard')

    return render(request, 'accounts/mechanic_dashboard.html')


@login_required
def customer_dashboard(request):
    if request.user.role != User.Role.CUSTOMER:
        return redirect('dashboard')

    return render(request, 'accounts/customer_dashboard.html')


@login_required
@require_POST
def user_logout(request):
    logout(request)
    return redirect('login')

def is_valid_email(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def customer_register(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':

        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if not all([full_name, username, email, phone_number, password1, password2]):
            messages.error(request, 'All fields are required.')

        elif password1 != password2:
            messages.error(request, 'Passwords do not match.')

        elif len(password1) < 8:
            messages.error(request, 'Password must contain at least 8 characters.')

        elif not any(char.isdigit() for char in password1):
            messages.error(request, 'Password must contain at least one number.')

        elif not any(char.isalpha() for char in password1):
            messages.error(request, 'Password must contain at least one letter.')

        elif User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'This username is already taken.')

        elif not is_valid_email(email):
            messages.error(request, 'Enter a valid email address.')

        elif User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'An account with this email already exists.')

        elif not (
            phone_number.isdigit()
            and len(phone_number) == 10
            and phone_number.startswith('0')
        ) and not (
            phone_number.startswith('+256')
            and phone_number[4:].isdigit()
            and len(phone_number[4:]) == 9
        ):
            messages.error(request, 'Enter a valid Ugandan phone number.')

        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=full_name,
                phone_number=phone_number,
                role=User.Role.CUSTOMER
            )

            login(request, user)
            return redirect('dashboard')

        return render(request, 'accounts/login.html', {
            'form': AuthenticationForm(),
            'show_register': True,
            'registration_data': {
                'full_name': full_name,
                'username': username,
                'email': email,
                'phone': phone_number,
            },
        })

    return redirect('login')
