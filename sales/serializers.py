from rest_framework import serializers

from .services import SalesOrderService, STATUS_TRANSITION_CHOICES


class SalesOrderLineSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = serializers.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)


class SalesOrderSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    order_number = serializers.CharField(max_length=50, read_only=True)
    customer_id = serializers.UUIDField()
    warehouse_id = serializers.UUIDField(required=False, allow_null=True)
    order_date = serializers.DateField()
    delivery_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=[
        ('DRAFT', 'Draft'),
        ('CONFIRMED', 'Confirmed'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled')
    ], default='DRAFT', required=False)
    stock_status = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    lines = SalesOrderLineSerializer(many=True)
    created_at = serializers.DateTimeField(read_only=True)

    def get_stock_status(self, obj):
        try:
            shortages = SalesOrderService.check_stock_availability(obj.id)
        except ValueError:
            return 'insufficient'

        if not shortages:
            return 'ok'

        total_lines = obj.lines.count()
        if total_lines and len(shortages) == total_lines:
            return 'insufficient'
        return 'partial'


class InvoiceSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    invoice_number = serializers.CharField(max_length=50, read_only=True)
    sales_order_id = serializers.UUIDField()
    customer_id = serializers.UUIDField()
    invoice_date = serializers.DateField()
    due_date = serializers.DateField()
    status = serializers.ChoiceField(choices=[
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled')
    ], default='DRAFT')
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = serializers.DateTimeField(read_only=True)


class SalesOrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=STATUS_TRANSITION_CHOICES)
