from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ReturnRequestViewSet

router = DefaultRouter()
router.register(r'returns', ReturnRequestViewSet, basename='return-request')

urlpatterns = [
    path('', include(router.urls)),
]

