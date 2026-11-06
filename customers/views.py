from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from accounts.models import User


@login_required
def customer_dashboard(request):

    if request.user.role != User.Role.CUSTOMER:
        return redirect('dashboard')

    return render(request, 'accounts/customer_dashboard.html')
