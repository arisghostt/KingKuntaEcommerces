from decimal import Decimal

from rest_framework import serializers

from products.models import Product

from .models import Coupon, Promotion


class PromotionSerializer(serializers.ModelSerializer):
    applicable_products = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), many=True, required=False)

    class Meta:
        model = Promotion
        fields = [
            'id',
            'name',
            'description',
            'type',
            'value',
            'start_date',
            'end_date',
            'usage_limit',
            'usage_count',
            'min_order_amount',
            'applicable_products',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']


class CouponSerializer(serializers.ModelSerializer):
    applicable_products = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), many=True, required=False)

    class Meta:
        model = Coupon
        fields = [
            'id',
            'code',
            'type',
            'value',
            'date_expiry',
            'usage_limit',
            'usage_count',
            'min_order_amount',
            'applicable_products',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']

    def validate_code(self, value):
        return value.strip().upper()


class CouponValidationSerializer(serializers.Serializer):
    code = serializers.CharField()
    order_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    product_ids = serializers.ListField(child=serializers.UUIDField(), required=False)

    def validate_code(self, value):
        return value.strip().upper()


class CouponValidationResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    coupon_id = serializers.UUIDField(allow_null=True)
    code = serializers.CharField(allow_null=True)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    reason = serializers.CharField(allow_blank=True)

    @staticmethod
    def build(coupon, order_amount, reason=''):
        discount_amount = Decimal('0.00')
        valid = coupon is not None and not reason
        code = coupon.code if coupon else None
        coupon_id = coupon.id if coupon else None
        if valid:
            if coupon.type == 'percent':
                discount_amount = (order_amount * coupon.value) / Decimal('100')
            else:
                discount_amount = min(order_amount, coupon.value)
        return {
            'valid': valid,
            'coupon_id': coupon_id,
            'code': code,
            'discount_amount': discount_amount.quantize(Decimal('0.01')),
            'reason': reason,
        }

