from django.core.management.base import BaseCommand
from django.utils import timezone
from products.models import Product
from inventory.models import StockMovement


class Command(BaseCommand):
    help = 'Crée les StockMovements initiaux pour les produits sans historique'

    def handle(self, *args, **options):
        created = 0
        skipped = 0

        for product in Product.objects.all():
            already_has_movements = StockMovement.objects.filter(product=product).exists()
            if already_has_movements:
                skipped += 1
                self.stdout.write(f'  SKIP: {product.name} (has existing movements)')
                continue

            stock_qty = int(product.current_stock or product.stock or 0)
            if stock_qty <= 0:
                skipped += 1
                self.stdout.write(f'  SKIP: {product.name} (stock = 0)')
                continue

            StockMovement.objects.create(
                product=product,
                type='in',
                quantity=stock_qty,
                reason='Initial stock',
                current_stock_after=stock_qty,
                created_by=None,
            )
            created += 1
            self.stdout.write(
                self.style.SUCCESS(f'  OK: {product.name} → {stock_qty} units')
            )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done: {created} movements created, {skipped} products skipped.'
        ))
