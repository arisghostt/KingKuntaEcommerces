from django.db import transaction
from .models import Payment
from sales.models import Invoice, SalesOrder


class PaymentService:
    @staticmethod
    @transaction.atomic
    def process_payment(payment_data):
        """
        Process payment and update related invoice and order status
        """
        # Create payment
        payment = Payment.objects.create(**payment_data)
        
        # Update invoice
        invoice = payment.invoice
        invoice.paid_amount += payment.amount
        
        # Update invoice status if fully paid
        if invoice.paid_amount >= invoice.total_amount:
            invoice.status = 'PAID'
        
        invoice.save()
        
        # Update sales order status if invoice is paid
        if invoice.status == 'PAID':
            sales_order = invoice.sales_order
            if sales_order.status == 'DRAFT':
                sales_order.status = 'CONFIRMED'
                sales_order.save()
        
        return payment