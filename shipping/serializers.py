from decimal import Decimal

from rest_framework import serializers

from sales.models import SalesOrder

from .models import Carrier, Shipment, ShippingZone


class CarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrier
        fields = [
            'id',
            'name',
            'code',
            'contact_email',
            'contact_phone',
            'tracking_url_template',
            'is_active',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ShippingZoneSerializer(serializers.ModelSerializer):
    countries = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = ShippingZone
        fields = [
            'id',
            'name',
            'code',
            'countries',
            'rate',
            'free_shipping_threshold',
            'estimated_days_min',
            'estimated_days_max',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ShipmentSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(source='order.id', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    carrier_name = serializers.CharField(source='carrier.name', read_only=True)
    zone_name = serializers.CharField(source='zone.name', read_only=True)

    class Meta:
        model = Shipment
        fields = [
            'id',
            'order_id',
            'order_number',
            'carrier',
            'carrier_name',
            'zone',
            'zone_name',
            'tracking_number',
            'status',
            'shipping_cost',
            'shipped_at',
            'delivered_at',
            'tracking_history',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'order_id', 'order_number', 'carrier_name', 'zone_name', 'created_at', 'updated_at']


class ShippingCalculationSerializer(serializers.Serializer):
    order_id = serializers.UUIDField(required=False)
    zone_id = serializers.UUIDField(required=False)
    country = serializers.CharField(required=False, allow_blank=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)

    def validate(self, attrs):
        if not attrs.get('order_id') and not attrs.get('zone_id') and not attrs.get('country'):
            raise serializers.ValidationError('order_id, zone_id or country is required.')
        if attrs.get('order_id') and not SalesOrder.objects.filter(pk=attrs['order_id']).exists():
            raise serializers.ValidationError({'order_id': 'Order not found.'})
        return attrs

    def resolve_zone(self):
        zone_id = self.validated_data.get('zone_id')
        country = (self.validated_data.get('country') or '').strip().lower()
        if zone_id:
            return ShippingZone.objects.filter(pk=zone_id, is_active=True).first()
        if country:
            for zone in ShippingZone.objects.filter(is_active=True):
                countries = [item.strip().lower() for item in zone.countries]
                if country in countries:
                    return zone
        return None

    def resolve_subtotal(self):
        subtotal = self.validated_data.get('subtotal')
        if subtotal is not None:
            return subtotal
        order_id = self.validated_data.get('order_id')
        if not order_id:
            return Decimal('0.00')
        order = SalesOrder.objects.filter(pk=order_id).first()
        return order.total_amount if order else Decimal('0.00')


class ShippingCalculationResponseSerializer(serializers.Serializer):
    zone_id = serializers.UUIDField(allow_null=True)
    zone = serializers.CharField(allow_null=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    shipping_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    free_shipping_applied = serializers.BooleanField()

