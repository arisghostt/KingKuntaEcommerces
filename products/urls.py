from django.urls import path

from .image_views import ProductImageUploadView
from .views import (
    CategoryDetailView,
    CategoryListCreateView,
    ProductDetailView,
    ProductGalleryImagesDeleteView,
    ProductListCreateView,
    ProductMainImageClearView,
    ProductVariantDetailView,
    ProductVariantListCreateView,
)

urlpatterns = [
    # 1. Routes fixes en premier (pas de <uuid>)
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/upload-image/', ProductImageUploadView.as_view(), name='product-image-upload'),
    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),

    # 2. Routes avec <uuid:pk> ensuite
    path('products/<uuid:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/<uuid:pk>/variants/', ProductVariantListCreateView.as_view(), name='product-variant-list-create'),
    path('products/<uuid:pk>/variants/<uuid:variant_id>/', ProductVariantDetailView.as_view(), name='product-variant-detail'),
    path('products/<uuid:pk>/gallery-images/delete/', ProductGalleryImagesDeleteView.as_view(), name='product-gallery-images-delete'),
    path('products/<uuid:pk>/main-image/clear/', ProductMainImageClearView.as_view(), name='product-main-image-clear'),

    # 3. Routes catégories avec <uuid:pk>
    path('categories/<uuid:pk>/', CategoryDetailView.as_view(), name='category-detail'),
]
