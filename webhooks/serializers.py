from rest_framework import serializers

from .models import WebhookEndpoint


class WebhookEndpointSerializer(serializers.ModelSerializer):
    events = serializers.ListField(child=serializers.ChoiceField(choices=WebhookEndpoint.EVENT_CHOICES))

    class Meta:
        model = WebhookEndpoint
        fields = [
            'id',
            'name',
            'url',
            'events',
            'secret',
            'is_active',
            'last_test_status',
            'last_test_response',
            'last_tested_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'secret',
            'last_test_status',
            'last_test_response',
            'last_tested_at',
            'created_at',
            'updated_at',
        ]

