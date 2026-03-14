from django.db import transaction
from .models import Payment
from sales.models import Invoice, SalesOrder


class PaymentService:
    @staticmethod
    @transaction.atomic
    def process_payment(payment_data):
        """
        Process payment and update related invoice
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
        
        return payment
