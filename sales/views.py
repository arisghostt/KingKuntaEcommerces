from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsSuperAdminOrHasModulePermission

from .models import SalesOrder
from .serializers import InvoiceSerializer, SalesOrderSerializer, SalesOrderStatusUpdateSerializer
from .services import SalesOrderService


class SalesOrderListCreateView(APIView):
    module_url = '/orders'
    permission_classes = [IsAuthenticated, IsSuperAdminOrHasModulePermission]

    @extend_schema(summary='List sales orders', responses={200: SalesOrderSerializer(many=True)}, tags=['Sales'])
    def get(self, request):
        from .models import SalesOrder

        orders = SalesOrder.objects.all()
        return Response(SalesOrderSerializer(orders, many=True).data)

    @extend_schema(
        summary='Create sales order',
        request=SalesOrderSerializer,
        responses={201: SalesOrderSerializer},
        examples=[OpenApiExample('Sales Order Example', value={'customer_id': '3fa85f64-5717-4562-b3fc-2c963f66afa6', 'order_date': '2024-01-15', 'tax_amount': '15.00', 'lines': []})],
        tags=['Sales'],
    )
    def post(self, request):
        import uuid

        serializer = SalesOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lines_data = serializer.validated_data.pop('lines', [])
        order_number = f"SO-{str(uuid.uuid4())[:8].upper()}"
        order_data = {**serializer.validated_data, 'order_number': order_number}
        order = SalesOrderService.create_sales_order(order_data, lines_data)
        return Response(SalesOrderSerializer(order).data, status=status.HTTP_201_CREATED)


class SalesOrderDetailView(APIView):
    module_url = '/orders'
    permission_classes = [IsAuthenticated, IsSuperAdminOrHasModulePermission]

    @extend_schema(summary='Get sales order', responses={200: SalesOrderSerializer}, tags=['Sales'])
    def get(self, request, pk):
        from .models import SalesOrder

        order = SalesOrder.objects.filter(pk=pk).first()
        if not order:
            return Response({'error': 'Sales order not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(SalesOrderSerializer(order).data)

    @extend_schema(summary='Update sales order', request=SalesOrderSerializer, responses={200: SalesOrderSerializer}, tags=['Sales'])
    def put(self, request, pk):

        new_status = request.data.get('status')
        if not new_status:
            return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            order = SalesOrderService.update_order_status(pk, new_status, request.user)
        except Exception as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SalesOrderSerializer(order).data)

    @extend_schema(summary='Delete sales order', responses={204: None}, tags=['Sales'])
    def delete(self, request, pk):
        from .models import SalesOrder

        order = SalesOrder.objects.filter(pk=pk).first()
        if not order:
            return Response({'error': 'Sales order not found'}, status=status.HTTP_404_NOT_FOUND)
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderStatusUpdateView(APIView):
    module_url = '/orders'
    required_action = 'is_edit'
    permission_classes = [IsAuthenticated, IsSuperAdminOrHasModulePermission]

    @extend_schema(
        summary='Change sales order status',
        request=SalesOrderStatusUpdateSerializer,
        responses={
            200: SalesOrderSerializer,
            400: {'description': 'Invalid transition or insufficient stock'},
            404: {'description': 'Sales order not found'},
        },
        tags=['Sales'],
    )
    def patch(self, request, pk):
        serializer = SalesOrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = SalesOrderService.update_order_status(pk, serializer.validated_data['status'], request.user)
        except SalesOrder.DoesNotExist:
            return Response({'error': 'Sales order not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SalesOrderSerializer(order).data)


class InvoiceListCreateView(APIView):
    module_url = '/invoices'
    permission_classes = [IsAuthenticated, IsSuperAdminOrHasModulePermission]

    @extend_schema(summary='List invoices', responses={200: InvoiceSerializer(many=True)}, tags=['Sales'])
    def get(self, request):
        from .models import Invoice

        invoices = Invoice.objects.all()
        return Response(InvoiceSerializer(invoices, many=True).data)

    @extend_schema(summary='Create invoice', request=InvoiceSerializer, responses={201: InvoiceSerializer}, tags=['Sales'])
    def post(self, request):
        import uuid
        from .models import Invoice

        serializer = InvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invoice_number = f"INV-{str(uuid.uuid4())[:8].upper()}"
        invoice = Invoice.objects.create(invoice_number=invoice_number, **serializer.validated_data)
        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)
