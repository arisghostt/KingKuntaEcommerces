from django.urls import path

from .views import AdminInventoryViewSet

admin_inventory_stats = AdminInventoryViewSet.as_view({'get': 'stats'})
admin_inventory_movements = AdminInventoryViewSet.as_view({'get': 'movements', 'post': 'create_movement'})
admin_inventory_alerts = AdminInventoryViewSet.as_view({'get': 'alerts'})
admin_inventory_restock = AdminInventoryViewSet.as_view({'patch': 'restock'})
admin_inventory_analytics = AdminInventoryViewSet.as_view({'get': 'analytics'})
admin_inventory_export = AdminInventoryViewSet.as_view({'get': 'export'})

urlpatterns = [
    path('inventory/stats/', admin_inventory_stats, name='admin-inventory-stats'),
    path('inventory/movements/', admin_inventory_movements, name='admin-inventory-movements'),
    path('inventory/alerts/', admin_inventory_alerts, name='admin-inventory-alerts'),
    path('inventory/alerts/<uuid:product_id>/restock/', admin_inventory_restock, name='admin-inventory-restock'),
    path('inventory/analytics/', admin_inventory_analytics, name='admin-inventory-analytics'),
    path('inventory/export/', admin_inventory_export, name='admin-inventory-export'),
]
