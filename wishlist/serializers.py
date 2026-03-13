from rest_framework import serializers

from products.models import Product
from products.serializers import ProductSerializer

from .models import WishlistItem


class WishlistItemSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(source='product', queryset=Product.objects.all())
    product = ProductSerializer(read_only=True)

    class Meta:
        model = WishlistItem
        fields = ['id', 'product_id', 'product', 'created_at']
        read_only_fields = ['id', 'product', 'created_at']

