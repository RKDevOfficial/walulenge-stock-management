from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from .forms import ProductForm
from .models import Category, Product, Supplier


def generate_product_code(category):
    prefix = ''.join(
        word[0:3].upper()
        for word in category.name.split()
    )
    base_code = f'WAS-{prefix}-'
    last_product = Product.objects.filter(
        category=category,
        product_code__startswith=base_code,
    ).order_by('-product_code').first()
    if last_product:
        try:
            last_number = int(last_product.product_code.split('-')[-1])
        except ValueError:
            last_number = 0
    else:
        last_number = 0

    number = last_number + 1
    code = f'{base_code}{number:04d}'
    while Product.objects.filter(product_code=code).exists():
        number += 1
        code = f'{base_code}{number:04d}'
    return code


@login_required
def product_list(request):
    if request.user.role != User.Role.MANAGER:
        return redirect('dashboard')

    search_query = request.GET.get('search', '').strip()
    products = Product.objects.select_related(
        'category'
    ).prefetch_related(
        'suppliers'
    ).order_by('name')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(product_code__icontains=search_query)
            | Q(category__name__icontains=search_query)
        )

    context = {
        'products': products,
        'search_query': search_query,
        'total_products': Product.objects.count(),
        'available_products': Product.objects.filter(
            is_available=True
        ).count(),
    }
    return render(request, 'products/product_list.html', context)


@login_required
def product_create(request):
    if request.user.role != User.Role.MANAGER:
        return redirect('dashboard')

    form = ProductForm(
        request.POST or None,
        request.FILES or None,
    )
    if request.method == 'POST':
        if form.is_valid():
            product = form.save(commit=False)
            if not product.product_code.strip():
                product.product_code = generate_product_code(product.category)
            product.save()
            form.save_m2m()
            messages.success(request, 'Product added successfully.')
            return redirect('product_list')
        else:
            messages.error(
                request,
                'Please correct the errors in the form.'
            )

    return render(request, 'products/product_form.html', {
        'form': form,
        'product': None,
        'categories': Category.objects.order_by('name'),
        'suppliers': Supplier.objects.order_by('name'),
        'page_title': 'Add Product',
        'button_text': 'Add Product',
        'submit_label': 'Add Product',
    })


@login_required
def product_update(request, pk):
    if request.user.role != User.Role.MANAGER:
        return redirect('dashboard')

    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Product updated successfully.')
        return redirect('product_list')

    return render(request, 'products/product_form.html', {
        'form': form,
        'product': product,
        'categories': Category.objects.order_by('name'),
        'suppliers': Supplier.objects.order_by('name'),
        'page_title': 'Edit Product',
        'button_text': 'Save Changes',
        'submit_label': 'Save Changes',
    })


@login_required
def product_delete(request, pk):
    if request.user.role != User.Role.MANAGER:
        return redirect('dashboard')

    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        try:
            product_name = product.name
            product.delete()
            messages.success(
                request,
                f'{product_name} deleted successfully.'
            )
            return redirect('product_list')
        except ProtectedError:
            messages.error(
                request,
                'This product cannot be deleted because it has existing stock or business records.'
            )
            return redirect('product_list')

    return render(
        request,
        'products/product_confirm_delete.html',
        {'product': product}
    )
