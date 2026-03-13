import uuid

from django.db import models

from core.models import BaseModel


class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Product(BaseModel):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('draft', 'Draft'),
    ]

    sku = models.CharField(max_length=50, unique=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    current_stock = models.IntegerField(default=0)
    min_stock = models.IntegerField(default=10)
    last_restocked = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    reviews = models.PositiveIntegerField(default=0)
    features = models.JSONField(default=list, blank=True)

    # ── Nouveaux champs (migration 0002) ─────────────────────────────────────
    brand = models.CharField(max_length=100, blank=True, default='')
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    dimensions = models.JSONField(default=dict, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    tags = models.JSONField(default=list, blank=True)
    # ─────────────────────────────────────────────────────────────────────────

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f'PRD-{uuid.uuid4().hex[:8].upper()}'
        if not self.current_stock and self.stock:
            self.current_stock = self.stock
        super().save(*args, **kwargs)

    def __str__(self):
        sku_prefix = f'{self.sku} - ' if self.sku else ''
        return f'{sku_prefix}{self.name}'


class ProductVariant(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=120)
    sku = models.CharField(max_length=50, unique=True, blank=True)
    attributes = models.JSONField(default=dict, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name', 'created_at']

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f'VAR-{uuid.uuid4().hex[:8].upper()}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.product.name} - {self.name}'


class ProductGalleryImage(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='products/gallery/')
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'created_at']

    def __str__(self):
        return f'{self.product.name} #{self.sort_order}'