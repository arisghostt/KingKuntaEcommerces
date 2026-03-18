from django.core.management.base import BaseCommand
from django.db import transaction

from inventory.models import StockMovement
from products.models import Product


class Command(BaseCommand):
    help = 'Create missing initial StockMovement entries for products with stock but no movement history'

    def handle(self, *args, **options):
        created_count = 0

        with transaction.atomic():
            for product in Product.objects.all().only('id', 'current_stock'):
                if StockMovement.objects.filter(product_id=product.id).exists():
                    continue

                current_stock = int(product.current_stock or 0)
                if current_stock <= 0:
                    continue

                StockMovement.objects.create(
                    product_id=product.id,
                    type='in',
                    quantity=current_stock,
                    reason='Initial stock',
                    current_stock_after=current_stock,
                    created_by=None,
                )
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Created {created_count} initial stock movement(s).'))

