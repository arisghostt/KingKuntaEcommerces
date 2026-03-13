"""Inventory API URLs"""
from django.urls import path

from . import views

urlpatterns = [
    path('adjustments/', views.InventoryAdjustmentView.as_view(), name='inventory-adjustment'),
    path('reception/', views.InventoryReceptionView.as_view(), name='inventory-reception'),
    path('stock/', views.InventoryStockListView.as_view(), name='inventory-stock-list'),
    path('stock/<uuid:product_id>/', views.InventoryStockDetailView.as_view(), name='inventory-stock-detail'),
]
