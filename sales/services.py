from django.db import transaction
from .models import SalesOrder, SalesOrderLine
from decimal import Decimal
from inventory.stock_service import StockService


class SalesOrderService:
    @staticmethod
    @transaction.atomic
    def create_sales_order(order_data, lines_data):
        """
        Create sales order with lines and calculate totals
        """
        # Create order
        order = SalesOrder.objects.create(**order_data)
        
        # Create lines and calculate totals
        subtotal = Decimal('0.00')
        for line_data in lines_data:
            line_total = line_data['quantity'] * line_data['unit_price'] * (1 - line_data.get('discount_percent', 0) / 100)
            SalesOrderLine.objects.create(
                sales_order=order,
                line_total=line_total,
                **line_data
            )
            subtotal += line_total
        
        # Update order totals
        order.subtotal = subtotal
        order.total_amount = subtotal + order.tax_amount
        order.save()
        
        return order
    
    @staticmethod
    @transaction.atomic
    def update_order_status(order_id, new_status, user=None):
        """
        Update order status and handle stock changes
        """
        order = SalesOrder.objects.get(id=order_id)
        old_status = order.status
        
        # Update status
        order.status = new_status
        order.save()
        
        # Handle stock changes based on status transition
        if old_status != 'SHIPPED' and new_status == 'SHIPPED':
            # Reduce stock when shipping
            StockService.process_sales_shipment(order, user)
        
        elif old_status == 'SHIPPED' and new_status == 'CANCELLED':
            # Restock when cancelling shipped order
            StockService.process_sales_cancellation(order, user)
        
        return order