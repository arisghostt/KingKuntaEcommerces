from rest_framework import serializers


class PaymentSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    payment_number = serializers.CharField(max_length=50, read_only=True)
    invoice_id = serializers.UUIDField()
    customer_id = serializers.UUIDField()
    payment_date = serializers.DateField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=[
        ('CASH', 'Cash'),
        ('CARD', 'Credit/Debit Card'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CHECK', 'Check'),
        ('OTHER', 'Other')
    ])
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField(read_only=True)


class ExpenseSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    expense_number = serializers.CharField(max_length=50, read_only=True)
    category = serializers.ChoiceField(choices=[
        ('OFFICE', 'Office Supplies'),
        ('TRAVEL', 'Travel'),
        ('UTILITIES', 'Utilities'),
        ('MARKETING', 'Marketing'),
        ('OTHER', 'Other')
    ])
    description = serializers.CharField(max_length=200)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    expense_date = serializers.DateField()
    supplier_id = serializers.UUIDField(required=False, allow_null=True)
    receipt_url = serializers.URLField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=[
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
        ('PAID', 'Paid'),
        ('REJECTED', 'Rejected')
    ], default='DRAFT')
    created_at = serializers.DateTimeField(read_only=True)


class FinancialReportSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(choices=[
        ('SALES_SUMMARY', 'Sales Summary'),
        ('PROFIT_LOSS', 'Profit & Loss'),
        ('CASH_FLOW', 'Cash Flow'),
        ('INVENTORY_VALUE', 'Inventory Valuation')
    ])
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    data = serializers.JSONField(read_only=True)
    generated_at = serializers.DateTimeField(read_only=True)