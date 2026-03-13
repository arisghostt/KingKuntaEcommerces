from django.conf import settings
from django.db import models
from django.db.models import Avg, Count

from core.models import BaseModel
from products.models import Product


class Review(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_reviews',
    )

    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'user']

    def __str__(self):
        return f'{self.product.name} - {self.rating}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.sync_product_stats(self.product_id)

    def delete(self, *args, **kwargs):
        product_id = self.product_id
        super().delete(*args, **kwargs)
        self.sync_product_stats(product_id)

    @classmethod
    def sync_product_stats(cls, product_id):
        stats = cls.objects.filter(product_id=product_id, is_approved=True).aggregate(avg=Avg('rating'), count=Count('id'))
        Product.objects.filter(pk=product_id).update(
            rating=stats['avg'] or 0,
            reviews=stats['count'] or 0,
        )

