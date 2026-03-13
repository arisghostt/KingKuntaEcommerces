from rest_framework import serializers


class CustomerSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    customer_code = serializers.CharField(max_length=50)
    company_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address = serializers.JSONField(required=False)
    credit_limit = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)


class SupplierSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    supplier_code = serializers.CharField(max_length=50)
    company_name = serializers.CharField(max_length=200)
    contact_person = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    address = serializers.JSONField(required=False)
    payment_terms = serializers.CharField(max_length=100, required=False)
    is_active = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)


class AddressSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    party_id = serializers.UUIDField()
    type = serializers.ChoiceField(choices=[('BILLING', 'Billing'), ('SHIPPING', 'Shipping')])
    street = serializers.CharField(max_length=200)
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=100)
    is_default = serializers.BooleanField(default=False)