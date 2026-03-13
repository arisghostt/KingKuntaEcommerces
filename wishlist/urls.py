from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import WishlistItemViewSet

router = DefaultRouter()
router.register(r'wishlist/items', WishlistItemViewSet, basename='wishlist-item')

wishlist_list = WishlistItemViewSet.as_view({'get': 'list'})

urlpatterns = [
    path('', include(router.urls)),
    path('wishlist/', wishlist_list, name='wishlist-list'),
]

