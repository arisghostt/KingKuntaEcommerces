from django.urls import path

from .views import ReviewViewSet

product_review_list = ReviewViewSet.as_view({'get': 'list', 'post': 'create'})
product_review_detail = ReviewViewSet.as_view({'put': 'update', 'delete': 'destroy'})

urlpatterns = [
    path('products/<uuid:product_id>/reviews/', product_review_list, name='product-review-list'),
    path('products/<uuid:product_id>/reviews/<uuid:review_id>/', product_review_detail, name='product-review-detail'),
]

