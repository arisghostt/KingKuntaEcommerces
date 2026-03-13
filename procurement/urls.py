from django.urls import path
from . import views

urlpatterns = [
    path('purchase-orders/', views.PurchaseOrderListCreateView.as_view(), name='purchase-order-list-create'),
    path('purchase-orders/<uuid:pk>/', views.PurchaseOrderDetailView.as_view(), name='purchase-order-detail'),
    path('goods-receipts/', views.GoodsReceiptListCreateView.as_view(), name='goods-receipt-list-create'),
]