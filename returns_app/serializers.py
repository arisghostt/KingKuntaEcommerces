from rest_framework import serializers

from sales.models import SalesOrder

from .models import ReturnRequest


class ReturnRequestSerializer(serializers.ModelSerializer):
    order_id = serializers.PrimaryKeyRelatedField(source='order', queryset=SalesOrder.objects.all())
    requester_id = serializers.UUIDField(source='requester.id', read_only=True)

    class Meta:
        model = ReturnRequest
        fields = [
            'id',
            'order_id',
            'requester_id',
            'items',
            'reason',
            'status',
            'refund_amount',
            'admin_notes',
            'reviewed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'requester_id', 'reviewed_at', 'created_at', 'updated_at']

    def validate_items(self, value):
        if not isinstance(value, list) or not value:
            raise serializers.ValidationError('Items must be a non-empty list.')
        return value

