from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CarrierViewSet, ShipmentTrackingView, ShippingCostCalculationView, ShippingZoneViewSet

router = DefaultRouter()
router.register(r'shipping/carriers', CarrierViewSet, basename='shipping-carrier')
router.register(r'shipping/zones', ShippingZoneViewSet, basename='shipping-zone')

urlpatterns = [
    path('', include(router.urls)),
    path('shipping/tracking/<uuid:order_id>/', ShipmentTrackingView.as_view(), name='shipping-tracking'),
    path('shipping/calculate/', ShippingCostCalculationView.as_view(), name='shipping-calculate'),
]

