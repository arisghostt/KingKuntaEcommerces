from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample
from .serializers import PaymentSerializer, ExpenseSerializer, FinancialReportSerializer


class PaymentListCreateView(APIView):
    @extend_schema(
        summary="List payments",
        responses={200: PaymentSerializer(many=True)},
        tags=['Finance']
    )
    def get(self, request):
        from .models import Payment
        payments = Payment.objects.all()
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create payment",
        request=PaymentSerializer,
        responses={201: PaymentSerializer},
        examples=[
            OpenApiExample(
                'Payment Example',
                value={
                    "invoice_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "customer_id": "3fa85f64-5717-4562-b3fc-2c963f66afa7",
                    "payment_date": "2024-01-20",
                    "amount": "214.98",
                    "payment_method": "BANK_TRANSFER",
                    "reference": "TXN123456",
                    "notes": "Payment for invoice INV-001"
                }
            )
        ],
        tags=['Finance']
    )
    def post(self, request):
        import uuid
        from .services import PaymentService
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            payment_number = f"PAY-{str(uuid.uuid4())[:8].upper()}"
            payment_data = {**serializer.validated_data, 'payment_number': payment_number}
            payment = PaymentService.process_payment(payment_data)
            response_serializer = PaymentSerializer(payment)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExpenseListCreateView(APIView):
    @extend_schema(
        summary="List expenses",
        responses={200: ExpenseSerializer(many=True)},
        tags=['Finance']
    )
    def get(self, request):
        from .models import Expense
        expenses = Expense.objects.all()
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create expense",
        request=ExpenseSerializer,
        responses={201: ExpenseSerializer},
        examples=[
            OpenApiExample(
                'Expense Example',
                value={
                    "category": "OFFICE",
                    "description": "Office supplies - printer paper",
                    "amount": "45.99",
                    "expense_date": "2024-01-15",
                    "supplier_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
                }
            )
        ],
        tags=['Finance']
    )
    def post(self, request):
        from .models import Expense
        import uuid
        serializer = ExpenseSerializer(data=request.data)
        if serializer.is_valid():
            expense_number = f"EXP-{str(uuid.uuid4())[:8].upper()}"
            expense = Expense.objects.create(expense_number=expense_number, **serializer.validated_data)
            response_serializer = ExpenseSerializer(expense)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FinancialReportView(APIView):
    @extend_schema(
        summary="Generate financial report",
        request=FinancialReportSerializer,
        responses={200: FinancialReportSerializer},
        examples=[
            OpenApiExample(
                'Profit & Loss Report',
                value={
                    "report_type": "PROFIT_LOSS",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31"
                }
            ),
            OpenApiExample(
                'Expense Summary Report',
                value={
                    "report_type": "EXPENSE_SUMMARY",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31"
                }
            )
        ],
        tags=['Finance']
    )
    def post(self, request):
        from .report_service import FinancialReportService
        from datetime import datetime
        
        report_type = request.data.get('report_type')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        report_data = FinancialReportService.generate_report(report_type, start_date, end_date)
        
        return Response({
            "report_type": report_type,
            "start_date": start_date,
            "end_date": end_date,
            "data": report_data,
            "generated_at": datetime.now().isoformat()
        })