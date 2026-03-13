from rest_framework import serializers

from products.models import Category, Product

from .models import Tax


class TaxSerializer(serializers.ModelSerializer):
    applicable_products = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), many=True, required=False)
    applicable_categories = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), many=True, required=False)

    class Meta:
        model = Tax
        fields = [
            'id',
            'name',
            'rate',
            'applicable_to',
            'applicable_products',
            'applicable_categories',
            'country',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

