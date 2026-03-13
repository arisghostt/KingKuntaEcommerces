from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample
from .serializers import PurchaseOrderSerializer, GoodsReceiptSerializer


class PurchaseOrderListCreateView(APIView):
    @extend_schema(
        summary="List purchase orders",
        responses={200: PurchaseOrderSerializer(many=True)},
        tags=['Procurement']
    )
    def get(self, request):
        from .models import PurchaseOrder
        orders = PurchaseOrder.objects.all()
        serializer = PurchaseOrderSerializer(orders, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create purchase order",
        request=PurchaseOrderSerializer,
        responses={201: PurchaseOrderSerializer},
        examples=[
            OpenApiExample(
                'Purchase Order Example',
                value={
                    "supplier_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "order_date": "2024-01-15",
                    "expected_date": "2024-01-25",
                    "tax_amount": "20.00",
                    "notes": "Urgent order",
                    "lines": [
                        {
                            "product_id": "3fa85f64-5717-4562-b3fc-2c963f66afa7",
                            "quantity": "10.00",
                            "unit_cost": "50.00"
                        }
                    ]
                }
            )
        ],
        tags=['Procurement']
    )
    def post(self, request):
        from .models import PurchaseOrder
        import uuid
        serializer = PurchaseOrderSerializer(data=request.data)
        if serializer.is_valid():
            lines_data = serializer.validated_data.pop('lines', [])
            po_number = f"PO-{str(uuid.uuid4())[:8].upper()}"
            order = PurchaseOrder.objects.create(po_number=po_number, **serializer.validated_data)
            from .models import PurchaseOrderLine
            for line_data in lines_data:
                line_total = line_data['quantity'] * line_data['unit_cost']
                PurchaseOrderLine.objects.create(purchase_order=order, line_total=line_total, **line_data)
            response_serializer = PurchaseOrderSerializer(order)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PurchaseOrderDetailView(APIView):
    @extend_schema(
        summary="Get purchase order",
        responses={200: PurchaseOrderSerializer},
        tags=['Procurement']
    )
    def get(self, request, pk):
        from .models import PurchaseOrder
        try:
            order = PurchaseOrder.objects.get(pk=pk)
            serializer = PurchaseOrderSerializer(order)
            return Response(serializer.data)
        except PurchaseOrder.DoesNotExist:
            return Response({'error': 'Purchase order not found'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        summary="Update purchase order",
        request=PurchaseOrderSerializer,
        responses={200: PurchaseOrderSerializer},
        tags=['Procurement']
    )
    def put(self, request, pk):
        return Response({})

    @extend_schema(
        summary="Delete purchase order",
        responses={204: None},
        tags=['Procurement']
    )
    def delete(self, request, pk):
        return Response(status=status.HTTP_204_NO_CONTENT)


class GoodsReceiptListCreateView(APIView):
    @extend_schema(
        summary="List goods receipts",
        responses={200: GoodsReceiptSerializer(many=True)},
        tags=['Procurement']
    )
    def get(self, request):
        from .models import GoodsReceipt
        receipts = GoodsReceipt.objects.all()
        serializer = GoodsReceiptSerializer(receipts, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create goods receipt",
        request=GoodsReceiptSerializer,
        responses={201: GoodsReceiptSerializer},
        examples=[
            OpenApiExample(
                'Goods Receipt Example',
                value={
                    "purchase_order_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "supplier_id": "3fa85f64-5717-4562-b3fc-2c963f66afa7",
                    "receipt_date": "2024-01-25",
                    "warehouse_id": "3fa85f64-5717-4562-b3fc-2c963f66afa8",
                    "notes": "All items received in good condition"
                }
            )
        ],
        tags=['Procurement']
    )
    def post(self, request):
        from .models import GoodsReceipt
        import uuid
        serializer = GoodsReceiptSerializer(data=request.data)
        if serializer.is_valid():
            receipt_number = f"GR-{str(uuid.uuid4())[:8].upper()}"
            receipt = GoodsReceipt.objects.create(receipt_number=receipt_number, **serializer.validated_data)
            response_serializer = GoodsReceiptSerializer(receipt)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)