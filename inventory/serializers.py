from rest_framework import serializers


class InventoryAdjustmentLineSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    warehouse_id = serializers.UUIDField()
    location_id = serializers.UUIDField(required=False, allow_null=True)
    batch_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    expires_on = serializers.DateField(required=False, allow_null=True)
    qty_delta = serializers.DecimalField(max_digits=10, decimal_places=2)


class InventoryAdjustmentInputSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=[
        ('CYCLE_COUNT', 'Cycle Count'),
        ('CORRECTION', 'Correction'),
        ('DAMAGE', 'Damage'),
        ('LOSS', 'Loss'),
        ('OTHER', 'Other'),
    ])
    note = serializers.CharField(required=False, allow_blank=True)
    lines = InventoryAdjustmentLineSerializer(many=True)


class InventoryAdjustmentOutputSerializer(serializers.Serializer):
    inventory_tx_ids = serializers.ListField(child=serializers.UUIDField())
    count = serializers.IntegerField()


class InventoryReceptionInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    supplier_id = serializers.UUIDField()
    warehouse_id = serializers.UUIDField()
    quantity_received = serializers.DecimalField(max_digits=10, decimal_places=2)
    date_received = serializers.DateField()
    reference_number = serializers.CharField(required=False, allow_blank=True)
    note = serializers.CharField(required=False, allow_blank=True)


class InventoryReceptionOutputSerializer(serializers.Serializer):
    reception_id = serializers.UUIDField()
    inventory_tx_id = serializers.UUIDField()