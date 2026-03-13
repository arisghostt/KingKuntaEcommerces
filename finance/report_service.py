from django.db.models import Sum, Q
from .models import Expense, Payment
from sales.models import Invoice
from decimal import Decimal


class FinancialReportService:
    @staticmethod
    def generate_report(report_type, start_date, end_date):
        """
        Generate financial reports excluding DRAFT expenses
        """
        if report_type == 'PROFIT_LOSS':
            return FinancialReportService._profit_loss_report(start_date, end_date)
        elif report_type == 'EXPENSE_SUMMARY':
            return FinancialReportService._expense_summary_report(start_date, end_date)
        elif report_type == 'CASH_FLOW':
            return FinancialReportService._cash_flow_report(start_date, end_date)
        else:
            return {"error": "Invalid report type"}
    
    @staticmethod
    def _profit_loss_report(start_date, end_date):
        """
        Profit & Loss report - excludes DRAFT expenses
        """
        # Revenue (from paid invoices)
        revenue = Invoice.objects.filter(
            invoice_date__range=[start_date, end_date],
            status='PAID'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # Expenses (only APPROVED and PAID expenses)
        expenses = Expense.objects.filter(
            expense_date__range=[start_date, end_date],
            status__in=['APPROVED', 'PAID']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        profit = revenue - expenses
        
        return {
            "revenue": str(revenue),
            "expenses": str(expenses),
            "profit": str(profit),
            "period": f"{start_date} to {end_date}"
        }
    
    @staticmethod
    def _expense_summary_report(start_date, end_date):
        """
        Expense summary by status - shows impact of DRAFT exclusion
        """
        # All expenses by status
        draft_expenses = Expense.objects.filter(
            expense_date__range=[start_date, end_date],
            status='DRAFT'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        approved_expenses = Expense.objects.filter(
            expense_date__range=[start_date, end_date],
            status__in=['APPROVED', 'PAID']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        pending_expenses = Expense.objects.filter(
            expense_date__range=[start_date, end_date],
            status='SUBMITTED'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        return {
            "draft_expenses": str(draft_expenses),
            "pending_expenses": str(pending_expenses),
            "approved_expenses": str(approved_expenses),
            "total_official": str(approved_expenses),
            "note": "Only approved/paid expenses are included in official reports"
        }
    
    @staticmethod
    def _cash_flow_report(start_date, end_date):
        """
        Cash flow report - actual money movements
        """
        # Cash inflows (payments received)
        cash_in = Payment.objects.filter(
            payment_date__range=[start_date, end_date]
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Cash outflows (only PAID expenses)
        cash_out = Expense.objects.filter(
            expense_date__range=[start_date, end_date],
            status='PAID'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        net_cash_flow = cash_in - cash_out
        
        return {
            "cash_inflows": str(cash_in),
            "cash_outflows": str(cash_out),
            "net_cash_flow": str(net_cash_flow),
            "note": "Only PAID expenses affect cash flow"
        }