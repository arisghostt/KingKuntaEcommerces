from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CouponViewSet, PromotionViewSet

router = DefaultRouter()
router.register(r'promotions', PromotionViewSet, basename='promotion')
router.register(r'promotions/coupons', CouponViewSet, basename='coupon')

urlpatterns = [
    path('', include(router.urls)),
]

