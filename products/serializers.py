from rest_framework import serializers

from .models import Category, Product, ProductGalleryImage, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    parent_id = serializers.PrimaryKeyRelatedField(source='parent', queryset=Category.objects.all(), allow_null=True, required=False)
    parent_name = serializers.CharField(source='parent.name', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'parent_id', 'parent_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        parent = attrs.get('parent')
        if self.instance and parent and parent.id == self.instance.id:
            raise serializers.ValidationError({'parent_id': 'A category cannot be its own parent.'})
        return attrs


class ProductGalleryImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ProductGalleryImage
        fields = ['id', 'url', 'sort_order', 'created_at']
        read_only_fields = ['id', 'url', 'created_at']

    def get_url(self, obj):
        request = self.context.get('request')
        if not obj.image:
            return None
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


class ProductVariantSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField(source='product.id', read_only=True)

    class Meta:
        model = ProductVariant
        fields = ['id', 'product_id', 'name', 'sku', 'attributes', 'price', 'stock', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'product_id', 'sku', 'created_at', 'updated_at']


class ProductSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        source='category',
        queryset=Category.objects.all(),
        allow_null=True,
        required=False,
    )
    category = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    gallery_images = serializers.SerializerMethodField()
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'description',
            'category_id', 'category',
            'price', 'cost_price', 'discount',
            'image', 'gallery_images',
            'stock', 'current_stock', 'min_stock', 'last_restocked',
            'status', 'rating', 'reviews',
            'features', 'brand', 'weight', 'dimensions', 'tags',
            'variants',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'current_stock', 'last_restocked',
            'image', 'gallery_images', 'variants',
            'rating', 'reviews',
            'created_at', 'updated_at',
        ]

    def get_category(self, obj):
        return obj.category.name if obj.category else None

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url

    def get_gallery_images(self, obj):
        serializer = ProductGalleryImageSerializer(
            obj.gallery_images.all(), many=True, context=self.context
        )
        return [item['url'] for item in serializer.data if item.get('url')]

    def create(self, validated_data):
        stock = validated_data.get('stock', 0)
        validated_data.setdefault('current_stock', stock)
        validated_data.setdefault('dimensions', {})
        validated_data.setdefault('tags', [])
        validated_data.setdefault('brand', '')
        validated_data.setdefault('discount', 0)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)