from django.contrib.auth import get_user_model
from rest_framework import serializers

from products.models import Product
from .models import CartItem, Event, Notification, Warehouse


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'code', 'name', 'address', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AuthTokenRequestSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)


class AuthTokenResponseSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=256)
    user_id = serializers.IntegerField()
    email = serializers.EmailField()


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            'id',
            'title',
            'description',
            'date',
            'time',
            'location',
            'category',
            'attendees',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_attendees(self, value):
        if value < 0:
            raise serializers.ValidationError('Attendees must be zero or positive.')
        return value


class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), write_only=True)

    class Meta:
        model = CartItem
        fields = [
            'id',
            'product',
            'product_id',
            'product_name',
            'product_price',
            'quantity',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'product_id', 'product_name', 'product_price', 'created_at', 'updated_at']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Quantity must be greater than zero.')
        return value


class NotificationSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='level', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'level', 'type', 'is_read', 'read_at', 'metadata', 'created_at']
        read_only_fields = ['id', 'is_read', 'read_at', 'created_at']


class AdminNotificationSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    type = serializers.CharField(source='level', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'user_id',
            'username',
            'email',
            'title',
            'message',
            'level',
            'type',
            'is_read',
            'read_at',
            'metadata',
            'created_at',
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def create(self, validated_data):
        user_model = get_user_model()
        return user_model.objects.create_user(**validated_data)
