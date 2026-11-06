from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),
    path('register/', views.customer_register, name='customer_register'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Role-based dashboards
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('shopkeeper/', views.shopkeeper_dashboard, name='shopkeeper_dashboard'),
    path('mechanic/', views.mechanic_dashboard, name='mechanic_dashboard'),
    path('logout/', views.user_logout, name='logout'),
]
