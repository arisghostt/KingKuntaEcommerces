from django.urls import path

from .views import (
    AuthRootView,
    AuthStatusView,
    CartItemCreateView,
    CartItemDetailView,
    CartView,
    CustomAuthToken,
    DashboardStatsView,
    EventDetailView,
    EventListCreateView,
    NotificationDeleteView,
    NotificationListView,
    NotificationReadView,
    WarehouseListCreateView,
)

urlpatterns = [
    path('auth/', AuthRootView.as_view(), name='auth_root'),
    path('auth/token/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('auth/status/', AuthStatusView.as_view(), name='auth_status'),
    path('events/', EventListCreateView.as_view(), name='event-list-create'),
    path('events/<uuid:pk>/', EventDetailView.as_view(), name='event-detail'),
    path('notifications/', NotificationListView.as_view(), name='notifications-list'),
    path('notifications/<uuid:pk>/read/', NotificationReadView.as_view(), name='notifications-read'),
    path('notifications/<uuid:pk>/', NotificationDeleteView.as_view(), name='notifications-delete'),
    path('cart/', CartView.as_view(), name='cart-detail'),
    path('cart/items/', CartItemCreateView.as_view(), name='cart-item-create'),
    path('cart/items/<uuid:pk>/', CartItemDetailView.as_view(), name='cart-item-detail'),
    path('warehouses/', WarehouseListCreateView.as_view(), name='warehouse-list-create'),
    path('api/dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
]
