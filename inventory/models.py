from django.conf import settings
from django.db import models

from core.models import BaseModel, Location, Warehouse
from parties.models import Supplier
from products.models import Product


class Stock(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_stocks')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True, blank=True)
    batch_code = models.CharField(max_length=100, blank=True)
    expires_on = models.DateField(null=True, blank=True)
    quantity_available = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_reserved = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ['product', 'warehouse', 'location', 'batch_code']

    def __str__(self):
        return f'{self.product} - {self.warehouse.code} - Qty: {self.quantity_available}'


class InventoryTx(BaseModel):
    DIRECTION_CHOICES = [
        ('IN', 'In'),
        ('OUT', 'Out'),
        ('ADJUST', 'Adjustment'),
    ]

    REASON_CHOICES = [
        ('PURCHASE', 'Purchase'),
        ('SALE', 'Sale'),
        ('CYCLE_COUNT', 'Cycle Count'),
        ('CORRECTION', 'Correction'),
        ('DAMAGE', 'Damage'),
        ('LOSS', 'Loss'),
        ('RECEPTION', 'Reception'),
        ('OTHER', 'Other'),
    ]

    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    reference_number = models.CharField(max_length=100, blank=True)
    note = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'{self.stock.product} - {self.direction} - {self.quantity}'


class InventoryReception(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2)
    date_received = models.DateField()
    reference_number = models.CharField(max_length=100, blank=True)
    note = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'{self.product} - {self.supplier.company_name} - {self.quantity_received}'


class StockMovement(BaseModel):
    TYPE_CHOICES = [
        ('in', 'In'),
        ('out', 'Out'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    type = models.CharField(max_length=3, choices=TYPE_CHOICES, db_index=True)
    quantity = models.PositiveIntegerField()
    reason = models.CharField(max_length=120)
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    current_stock_after = models.IntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='stock_movements_created',
    )

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['product', 'type', 'date']),
            models.Index(fields=['type', 'date']),
        ]

    def __str__(self):
        return f'{self.product} - {self.type} - {self.quantity}'
