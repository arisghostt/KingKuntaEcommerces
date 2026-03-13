from rest_framework import serializers


class PurchaseOrderLineSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)


class PurchaseOrderSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    po_number = serializers.CharField(max_length=50, read_only=True)
    supplier_id = serializers.UUIDField()
    order_date = serializers.DateField()
    expected_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=[
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('CONFIRMED', 'Confirmed'),
        ('RECEIVED', 'Received'),
        ('CANCELLED', 'Cancelled')
    ], default='DRAFT')
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    lines = PurchaseOrderLineSerializer(many=True)
    created_at = serializers.DateTimeField(read_only=True)


class GoodsReceiptSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    receipt_number = serializers.CharField(max_length=50, read_only=True)
    purchase_order_id = serializers.UUIDField()
    supplier_id = serializers.UUIDField()
    receipt_date = serializers.DateField()
    warehouse_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=[
        ('DRAFT', 'Draft'),
        ('CONFIRMED', 'Confirmed'),
        ('POSTED', 'Posted')
    ], default='DRAFT')
    notes = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField(read_only=True)