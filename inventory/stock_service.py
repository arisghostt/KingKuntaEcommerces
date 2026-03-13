from django.db import transaction
from .models import Stock, InventoryTx


class StockService:
    @staticmethod
    @transaction.atomic
    def process_sales_shipment(sales_order, user=None):
        """
        Reduce stock when order is shipped
        """
        if not sales_order.warehouse:
            raise ValueError("Sales order must have a warehouse assigned")
            
        for line in sales_order.lines.all():
            # Get or create stock record
            stock, created = Stock.objects.get_or_create(
                product=line.product,
                warehouse=sales_order.warehouse,
                location=None,
                batch_code='',
                defaults={'quantity_available': 0}
            )
            
            # Check if enough stock available
            if stock.quantity_available < line.quantity:
                raise ValueError(f"Insufficient stock for {line.product.sku}. Available: {stock.quantity_available}, Required: {line.quantity}")
            
            # Reduce stock
            stock.quantity_available -= line.quantity
            stock.save()
            
            # Create inventory transaction
            InventoryTx.objects.create(
                stock=stock,
                direction='OUT',
                reason='SALE',
                quantity=line.quantity,
                reference_number=sales_order.order_number,
                note=f"Sale shipment for order {sales_order.order_number}",
                user=user
            )
    
    @staticmethod
    @transaction.atomic
    def process_sales_cancellation(sales_order, user=None):
        """
        Restock when order is cancelled (only if it was shipped)
        """
        if not sales_order.warehouse:
            return  # Skip if no warehouse assigned
            
        # Check if order was shipped (has inventory transactions)
        shipped_transactions = InventoryTx.objects.filter(
            reference_number=sales_order.order_number,
            reason='SALE',
            direction='OUT'
        )
        
        if shipped_transactions.exists():
            for line in sales_order.lines.all():
                # Get stock record
                try:
                    stock = Stock.objects.get(
                        product=line.product,
                        warehouse=sales_order.warehouse,
                        location=None,
                        batch_code=''
                    )
                    
                    # Restock
                    stock.quantity_available += line.quantity
                    stock.save()
                    
                    # Create inventory transaction
                    InventoryTx.objects.create(
                        stock=stock,
                        direction='IN',
                        reason='CORRECTION',
                        quantity=line.quantity,
                        reference_number=sales_order.order_number,
                        note=f"Restock due to order cancellation {sales_order.order_number}",
                        user=user
                    )
                except Stock.DoesNotExist:
                    # Create stock record if it doesn't exist
                    stock = Stock.objects.create(
                        product=line.product,
                        warehouse=sales_order.warehouse,
                        location=None,
                        batch_code='',
                        quantity_available=line.quantity
                    )
                    
                    InventoryTx.objects.create(
                        stock=stock,
                        direction='IN',
                        reason='CORRECTION',
                        quantity=line.quantity,
                        reference_number=sales_order.order_number,
                        note=f"Restock due to order cancellation {sales_order.order_number}",
                        user=user
                    )