from django.urls import path
from . import views

urlpatterns = [
    path('orders/', views.SalesOrderListCreateView.as_view(), name='sales-order-list-create'),
    path('orders/<uuid:pk>/', views.SalesOrderDetailView.as_view(), name='sales-order-detail'),
    path('invoices/', views.InvoiceListCreateView.as_view(), name='invoice-list-create'),
]