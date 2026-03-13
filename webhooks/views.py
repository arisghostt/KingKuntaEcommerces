import json
import urllib.error
import urllib.request

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import WebhookEndpoint
from .serializers import WebhookEndpointSerializer


class WebhookEndpointViewSet(viewsets.ModelViewSet):
    queryset = WebhookEndpoint.objects.all()
    serializer_class = WebhookEndpointSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def test_webhook(self, request, pk=None):
        webhook = self.get_queryset().filter(pk=pk).first()
        if not webhook:
            return Response({'error': 'Webhook not found'}, status=status.HTTP_404_NOT_FOUND)

        payload = {
            'event': (webhook.events or ['order.created'])[0],
            'message': 'KingKunta webhook test',
            'timestamp': timezone.now().isoformat(),
        }
        req = urllib.request.Request(
            webhook.url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'X-KingKunta-Signature': webhook.secret,
            },
            method='POST',
        )

        status_label = 'success'
        response_body = ''
        status_code = status.HTTP_200_OK

        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                response_body = response.read().decode('utf-8', errors='ignore')[:500]
        except urllib.error.URLError as exc:
            status_label = 'failed'
            response_body = str(exc.reason)
            status_code = status.HTTP_502_BAD_GATEWAY

        webhook.last_test_status = status_label
        webhook.last_test_response = response_body
        webhook.last_tested_at = timezone.now()
        webhook.save(update_fields=['last_test_status', 'last_test_response', 'last_tested_at', 'updated_at'])

        return Response(
            {
                'status': status_label,
                'webhook_id': str(webhook.id),
                'payload': payload,
                'response': response_body,
            },
            status=status_code,
        )

