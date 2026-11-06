from django.urls import path

from . import views


urlpatterns = [
    path('', views.stock_list, name='stock_list'),
    path('add/', views.stock_add, name='stock_add'),
    path('remove/', views.stock_remove, name='stock_remove'),
    path('transactions/', views.stock_transactions, name='stock_transactions'),
    path('transfers/', views.stock_transfer_list, name='stock_transfer_list'),
    path('transfers/create/', views.stock_transfer_create, name='stock_transfer_create'),
    path('transfers/<int:pk>/', views.stock_transfer_detail, name='stock_transfer_detail'),
    path('transfers/<int:pk>/send/', views.stock_transfer_send, name='stock_transfer_send'),
    path('transfers/<int:pk>/receive/', views.stock_transfer_receive, name='stock_transfer_receive'),
    path('transfers/<int:pk>/cancel/', views.stock_transfer_cancel, name='stock_transfer_cancel'),
]
