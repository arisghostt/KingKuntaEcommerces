"""
Inventory business logic services
"""
from decimal import Decimal

from django.db import transaction
from .models import InventoryReception, Stock, InventoryTx
from products.models import Product
from parties.models import Supplier
from core.models import Location, Warehouse


class InventoryAdjustmentService:
    """Service class for handling inventory adjustments"""
    
    @staticmethod
    @transaction.atomic
    def process_adjustment(user, reason, note, lines_data):
        """
        Process inventory adjustment
        
        Args:
            user: User instance
            reason: Adjustment reason
            note: Optional note
            lines_data: List of adjustment line data
            
        Returns:
            dict: Result with inventory_tx_ids and count
        """
        inventory_tx_ids = []

        for line in lines_data:
            product = Product.objects.get(id=line['product_id'])
            warehouse = Warehouse.objects.get(id=line['warehouse_id'])
            location = None
            if line.get('location_id'):
                location = Location.objects.get(id=line['location_id'])
            batch_code = line.get('batch_code') or ''
            expires_on = line.get('expires_on')
            qty_delta = Decimal(line['qty_delta'])

            if qty_delta == 0:
                continue

            stock_qs = Stock.objects.select_for_update().filter(
                product=product,
                warehouse=warehouse,
                location=location,
                batch_code=batch_code,
            )
            stock = stock_qs.first()

            if not stock:
                if qty_delta < 0:
                    raise ValueError(
                        f"Cannot decrease stock for {product.sku} in {warehouse.code}; no existing record."
                    )
                stock = Stock.objects.create(
                    product=product,
                    warehouse=warehouse,
                    location=location,
                    batch_code=batch_code,
                    expires_on=expires_on,
                    quantity_available=Decimal('0'),
                )

            new_available = stock.quantity_available + qty_delta

            if new_available < 0:
                raise ValueError(
                    f"Adjustment would reduce {product.sku} below zero in {warehouse.code}."
                )

            if new_available < stock.quantity_reserved:
                raise ValueError(
                    f"Adjustment would reduce {product.sku} below reserved quantity in {warehouse.code}."
                )

            stock.quantity_available = new_available
            if expires_on is not None:
                stock.expires_on = expires_on
            stock.save()

            inventory_tx = InventoryTx.objects.create(
                stock=stock,
                direction='ADJUST',
                reason=reason,
                quantity=abs(qty_delta),
                reference_number='',
                note=note or '',
                user=user,
            )
            inventory_tx_ids.append(inventory_tx.id)

        return {
            'inventory_tx_ids': inventory_tx_ids,
            'count': len(inventory_tx_ids),
        }


class InventoryReceptionService:
    """Service class for handling inventory reception"""
    
    @staticmethod
    @transaction.atomic
    def process_reception(user, product_id, supplier_id, warehouse_id, quantity_received, date_received, reference_number='', note=''):
        """
        Process inventory reception
        
        Args:
            user: User instance
            product_id: Product UUID
            supplier_id: Supplier UUID
            warehouse_id: Warehouse UUID
            quantity_received: Decimal quantity
            date_received: Date of reception
            reference_number: Optional reference
            note: Optional note
            
        Returns:
            dict: Result with reception_id and inventory_tx_id
        """
        # Get related objects
        product = Product.objects.get(id=product_id)
        supplier = Supplier.objects.get(id=supplier_id)
        warehouse = Warehouse.objects.get(id=warehouse_id)
        
        # Create reception record
        reception = InventoryReception.objects.create(
            product=product,
            supplier=supplier,
            warehouse=warehouse,
            quantity_received=quantity_received,
            date_received=date_received,
            reference_number=reference_number,
            note=note,
            user=user
        )
        
        # Get or create stock record
        stock, created = Stock.objects.get_or_create(
            product=product,
            warehouse=warehouse,
            location=None,
            batch_code='',
            defaults={'quantity_available': 0}
        )
        
        # Update stock quantity
        stock.quantity_available += quantity_received
        stock.save()
        
        # Create inventory transaction
        inventory_tx = InventoryTx.objects.create(
            stock=stock,
            direction='IN',
            reason='RECEPTION',
            quantity=quantity_received,
            reference_number=reference_number,
            note=note,
            user=user
        )
        
        return {
            'reception_id': reception.id,
            'inventory_tx_id': inventory_tx.id
        }
