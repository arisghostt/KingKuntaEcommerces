from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import WebhookEndpointViewSet

router = DefaultRouter()
router.register(r'webhooks', WebhookEndpointViewSet, basename='webhook')

webhook_test = WebhookEndpointViewSet.as_view({'post': 'test_webhook'})

urlpatterns = [
    path('', include(router.urls)),
    path('webhooks/test/<uuid:pk>/', webhook_test, name='webhook-test'),
]

