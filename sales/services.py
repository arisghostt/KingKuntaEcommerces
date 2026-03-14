import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from .models import SalesOrder, SalesOrderLine
from inventory.models import Stock
from inventory.stock_service import StockService

STATUS_TRANSITION_CHOICES = [
    ('CONFIRMED', 'Confirmed'),
    ('SHIPPED', 'Shipped'),
    ('DELIVERED', 'Delivered'),
    ('CANCELLED', 'Cancelled'),
]
ALLOWED_STATUS_TRANSITIONS = {
    'DRAFT': ['CONFIRMED'],
    'CONFIRMED': ['SHIPPED', 'CANCELLED'],
    'SHIPPED': ['DELIVERED', 'CANCELLED'],
}

logger = logging.getLogger(__name__)


class SalesOrderService:
    @staticmethod
    def is_transition_allowed(old_status, new_status):
        if old_status == new_status:
            return True
        return new_status in ALLOWED_STATUS_TRANSITIONS.get(old_status, [])

    @staticmethod
    @transaction.atomic
    def create_sales_order(order_data, lines_data):
        """
        Create sales order with lines and calculate totals
        """
        if not order_data.get('warehouse_id') and not order_data.get('warehouse'):
            logger.warning(
                "Creating sales order %s without warehouse assignment; inventory cannot be reserved until a warehouse is set.",
                order_data.get('order_number', '<pending>'),
            )
        # Create order
        order = SalesOrder.objects.create(**order_data)

        # Create lines and calculate totals
        subtotal = Decimal('0.00')
        for line_data in lines_data:
            discount_percent = Decimal(line_data.get('discount_percent', 0))
            discount_multiplier = Decimal('1') - (discount_percent / Decimal('100'))
            line_total = line_data['quantity'] * line_data['unit_price'] * discount_multiplier
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
    def check_stock_availability(order_id):
        """Return a list of shortage details for the given order"""
        order = (
            SalesOrder.objects.select_related('warehouse')
            .prefetch_related('lines__product')
            .get(id=order_id)
        )
        if not order.warehouse:
            raise ValueError('Assign a warehouse to the order before confirming it.')

        shortages = []
        for line in order.lines.all():
            total_available = (
                Stock.objects.filter(product=line.product, warehouse=order.warehouse)
                .aggregate(total=Sum('quantity_available'))
                .get('total')
            ) or Decimal('0')
            if total_available < line.quantity:
                shortages.append({
                    'product_id': str(line.product_id),
                    'sku': line.product.sku,
                    'required': line.quantity,
                    'available': total_available,
                })
        return shortages

    @staticmethod
    @transaction.atomic
    def update_order_status(order_id, new_status, user=None):
        """
        Update order status and handle stock changes
        """
        order = SalesOrder.objects.select_for_update().get(id=order_id)
        old_status = order.status

        if not SalesOrderService.is_transition_allowed(old_status, new_status):
            raise ValueError(f"Transition from {old_status} to {new_status} is not allowed.")

        if old_status == 'DRAFT' and new_status == 'CONFIRMED':
            shortages = SalesOrderService.check_stock_availability(order_id)
            if shortages:
                details = ', '.join(
                    [f"{item['sku']} (avail {item['available']})" for item in shortages]
                )
                raise ValueError(f"Insufficient stock for products: {details}")

        if old_status == new_status:
            return order

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
