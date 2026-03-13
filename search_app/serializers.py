from rest_framework import serializers

from products.serializers import CategorySerializer, ProductSerializer


class SearchResultSerializer(serializers.Serializer):
    products = ProductSerializer(many=True)
    categories = CategorySerializer(many=True)
    count = serializers.IntegerField()

