from django.urls import path

from .views import OrderStatusUpdateView, SalesOrderDetailView, SalesOrderListCreateView

urlpatterns = [
    path('orders/', SalesOrderListCreateView.as_view(), name='admin-order-list'),
    path('orders/<uuid:pk>/', SalesOrderDetailView.as_view(), name='admin-order-detail'),
    path('orders/<uuid:pk>/status/', OrderStatusUpdateView.as_view(), name='admin-order-status'),
]
