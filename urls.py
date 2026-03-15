"""
URL configuration for KingKuntaEcommerce project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from auth_views import (
    CurrentUserView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetView,
    RegisterView,
    SafeTokenObtainPairView,
    SafeTokenRefreshView,
)
from core.views import AdminNotificationListView


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API endpoints
    path('api/auth/login/', SafeTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/me/', CurrentUserView.as_view(), name='auth-me'),
    path('api/auth/refresh/', SafeTokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/register/', RegisterView.as_view(), name='auth-register'),
    path('api/auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('api/auth/password-reset/', PasswordResetView.as_view(), name='auth-password-reset'),
    path('api/auth/password-reset-confirm/', PasswordResetConfirmView.as_view(), name='auth-password-reset-confirm'),
    path('api/admin/notifications/', AdminNotificationListView.as_view(), name='admin-notifications-list'),
    path('api/admin/', include('reviews.admin_urls')),
    path('api/admin/', include('promotions.admin_urls')),
    path('api/admin/', include('parties.admin_urls')),
    path('api/admin/', include('sales.admin_urls')),
    path('api/', include('users.urls')),
    path('api/admin/', include('core.admin_urls')),
    path('api/', include('core.urls')),
    path('api/', include('products.urls')),
    path('api/', include('shipping.urls')),
    path('api/', include('promotions.urls')),
    path('api/', include('reviews.urls')),
    path('api/', include('wishlist.urls')),
    path('api/', include('returns_app.urls')),
    path('api/', include('search_app.urls')),
    path('api/', include('taxes.urls')),
    path('api/', include('webhooks.urls')),
    path('api/admin/', include('inventory.admin_urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/parties/', include('parties.urls')),
    path('api/sales/', include('sales.urls')),
    path('api/procurement/', include('procurement.urls')),
    path('api/finance/', include('finance.urls')),
]

# Serve media files in development (only if NOT using R2)
# If USE_R2 is enabled, MEDIA_URL points to R2 endpoints and MEDIA_ROOT is empty,
# so Django's static() helper would raise an error.
if settings.DEBUG and not getattr(settings, 'USE_R2', False):
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
