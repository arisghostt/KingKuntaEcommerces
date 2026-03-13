import secrets

from django.db import models

from core.models import BaseModel


class WebhookEndpoint(BaseModel):
    EVENT_CHOICES = [
        ('order.created', 'order.created'),
        ('order.paid', 'order.paid'),
        ('order.shipped', 'order.shipped'),
        ('payment.received', 'payment.received'),
        ('stock.low', 'stock.low'),
    ]

    name = models.CharField(max_length=120)
    url = models.URLField()
    events = models.JSONField(default=list, blank=True)
    secret = models.CharField(max_length=80, default=secrets.token_hex, editable=False)
    is_active = models.BooleanField(default=True)
    last_test_status = models.CharField(max_length=20, blank=True)
    last_test_response = models.TextField(blank=True)
    last_tested_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

