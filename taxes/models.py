from django.db import models

from core.models import BaseModel


class Tax(BaseModel):
    APPLICABLE_TO_CHOICES = [
        ('products', 'Products'),
        ('categories', 'Categories'),
        ('both', 'Both'),
    ]

    name = models.CharField(max_length=120)
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    applicable_to = models.CharField(max_length=20, choices=APPLICABLE_TO_CHOICES)
    applicable_products = models.ManyToManyField('products.Product', blank=True, related_name='taxes')
    applicable_categories = models.ManyToManyField('products.Category', blank=True, related_name='taxes')
    country = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.country})'

