"""
Inventory API views
"""
import csv
from datetime import timedelta
from django.db import models
from django.http import HttpResponse
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import Product
from users.permissions import IsSuperAdmin, IsSuperAdminOrHasModulePermission

from .models import StockMovement
from .serializers import (
    InventoryAdjustmentInputSerializer,
    InventoryAdjustmentOutputSerializer,
    InventoryReceptionInputSerializer,
    InventoryReceptionOutputSerializer,
)
from .services import InventoryAdjustmentService, InventoryReceptionService


class InventoryAdjustmentView(APIView):
    """
    Create inventory adjustments (cycle counts, corrections)
    """

    @extend_schema(
        summary='Create inventory adjustment',
        description="""
        Creates inventory adjustments for cycle counts, corrections, or other reasons.

        **Process:**
        1. Validates adjustment reason
        2. For each line, validates stock availability (if decreasing)
        3. Creates inventory transactions (ADJUST direction)
        4. Updates or creates stock records

        **Business Rules:**
        - Positive qty_delta = increase stock
        - Negative qty_delta = decrease stock
        - Cannot decrease stock below zero or reserved quantity
        - Each adjustment creates a full audit trail via InventoryTx
        """,
        request=InventoryAdjustmentInputSerializer,
        responses={
            201: InventoryAdjustmentOutputSerializer,
            400: {'description': 'Validation error'},
        },
        examples=[
            OpenApiExample(
                'Adjustment Example',
                value={
                    'reason': 'CYCLE_COUNT',
                    'note': 'Annual inventory count - variance adjustments',
                    'lines': [
                        {
                            'product_id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                            'warehouse_id': '3fa85f64-5717-4562-b3fc-2c963f66afa7',
                            'location_id': '3fa85f64-5717-4562-b3fc-2c963f66afa8',
                            'batch_code': None,
                            'expires_on': None,
                            'qty_delta': -2.0,
                        }
                    ],
                },
                request_only=True,
            )
        ],
        tags=['Inventory'],
    )
    def post(self, request):
        serializer = InventoryAdjustmentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = InventoryAdjustmentService.process_adjustment(
            user=request.user,
            reason=serializer.validated_data['reason'],
            note=serializer.validated_data.get('note', ''),
            lines_data=serializer.validated_data['lines'],
        )

        output_serializer = InventoryAdjustmentOutputSerializer(result)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class InventoryReceptionView(APIView):
    """
    Create inventory reception records
    """

    @extend_schema(
        summary='Create inventory reception',
        request=InventoryReceptionInputSerializer,
        responses={201: InventoryReceptionOutputSerializer, 400: {'description': 'Validation error'}},
        tags=['Inventory'],
    )
    def post(self, request):
        serializer = InventoryReceptionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = InventoryReceptionService.process_reception(
            user=request.user,
            **serializer.validated_data,
        )

        output_serializer = InventoryReceptionOutputSerializer(result)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)




class InventoryStockListView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    @extend_schema(summary='Global stock snapshot', tags=['Inventory'])
    def get(self, request):
        products = Product.objects.all().order_by('name')
        payload = [
            {
                'product_id': str(product.id),
                'name': product.name,
                'sku': product.sku,
                'stock': product.stock,
                'current_stock': product.current_stock,
                'min_stock': product.min_stock,
                'status': product.status,
            }
            for product in products
        ]
        return Response(payload)


class InventoryStockDetailView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    @extend_schema(summary='Stock for one product', tags=['Inventory'])
    def get(self, request, product_id):
        product = Product.objects.filter(pk=product_id).first()
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                'product_id': str(product.id),
                'name': product.name,
                'sku': product.sku,
                'stock': product.stock,
                'current_stock': product.current_stock,
                'min_stock': product.min_stock,
                'status': product.status,
                'last_restocked': product.last_restocked,
            }
        )


class AdminInventoryPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class AdminInventoryViewSet(viewsets.ViewSet):
    module_url = '/inventory'
    pagination_class = AdminInventoryPagination

    def get_permissions(self):
        return [IsAuthenticated(), IsSuperAdminOrHasModulePermission()]

    def _paginate(self, request, items):
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(items, request, view=self)
        if page is None:
            return Response({'count': len(items), 'results': items})
        return paginator.get_paginated_response(page)

    def _serialize_movement(self, movement):
        return {
            'id': str(movement.id),
            'date': movement.date,
            'product_id': str(movement.product_id),
            'product': movement.product.name,
            'category': movement.product.category.name if movement.product.category else None,
            'type': movement.type,
            'quantity': movement.quantity,
            'reason': movement.reason,
            'current_stock_after': movement.current_stock_after,
            'created_by': movement.created_by.username if movement.created_by else None,
        }

    @extend_schema(summary='Inventory dashboard stats', tags=['admin'])
    def stats(self, request):
        products = Product.objects.all()
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        stock_in_month = (
            StockMovement.objects.filter(type='in', date__gte=last_30_days)
            .aggregate(total=models.Sum('quantity'))
            .get('total')
            or 0
        )
        stock_out_month = (
            StockMovement.objects.filter(type='out', date__gte=last_30_days)
            .aggregate(total=models.Sum('quantity'))
            .get('total')
            or 0
        )
        low_stock_count = products.filter(current_stock__gt=0, current_stock__lte=models.F('min_stock')).count()
        out_of_stock_count = products.filter(current_stock__lte=0).count()
        prev_30_days_start = now - timedelta(days=60)
        stock_in_prev = (
            StockMovement.objects.filter(type='in', date__gte=prev_30_days_start, date__lt=last_30_days)
            .aggregate(total=models.Sum('quantity'))
            .get('total')
            or 0
        )
        stock_out_prev = (
            StockMovement.objects.filter(type='out', date__gte=prev_30_days_start, date__lt=last_30_days)
            .aggregate(total=models.Sum('quantity'))
            .get('total')
            or 0
        )
        products_this_month = Product.objects.filter(created_at__gte=last_30_days).count()
        products_prev_month = Product.objects.filter(
            created_at__gte=prev_30_days_start, created_at__lt=last_30_days
        ).count()
        low_stock_prev = products.filter(
            current_stock__gt=0,
            current_stock__lte=models.F('min_stock'),
            updated_at__gte=prev_30_days_start,
            updated_at__lt=last_30_days,
        ).count()
        total_products_change = products_this_month - products_prev_month
        stock_in_change = stock_in_month - stock_in_prev
        stock_out_change = stock_out_month - stock_out_prev
        low_stock_change = low_stock_count - low_stock_prev

        return Response(
            {
                'total_products': products.count(),
                'stock_in_month': stock_in_month,
                'stock_out_month': stock_out_month,
                'low_stock_count': low_stock_count,
                'out_of_stock_count': out_of_stock_count,
                'total_products_change': total_products_change,
                'stock_in_change': stock_in_change,
                'stock_out_change': stock_out_change,
                'low_stock_change': low_stock_change,
            }
        )

    @extend_schema(summary='List stock movements', tags=['admin'])
    def movements(self, request):
        queryset = StockMovement.objects.select_related('product', 'product__category', 'created_by')
        type_filter = request.query_params.get('type')
        search = request.query_params.get('search')

        if type_filter in {'in', 'out'}:
            queryset = queryset.filter(type=type_filter)
        if search:
            queryset = queryset.filter(product__name__icontains=search)

        items = [self._serialize_movement(movement) for movement in queryset]
        return self._paginate(request, items)

    @extend_schema(summary='Create stock movement', tags=['admin'])
    def create_movement(self, request):
        product_id = request.data.get('product_id')
        movement_type = request.data.get('type')
        quantity = request.data.get('quantity')
        reason = request.data.get('reason', '').strip() or 'Manual adjustment'

        if not product_id or movement_type not in {'in', 'out'} or quantity in (None, ''):
            return Response({'error': 'product_id, type and quantity are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return Response({'error': 'Quantity must be a positive integer.'}, status=status.HTTP_400_BAD_REQUEST)

        if quantity <= 0:
            return Response({'error': 'Quantity must be a positive integer.'}, status=status.HTTP_400_BAD_REQUEST)

        product = Product.objects.filter(pk=product_id).first()
        if not product:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        current_stock = int(product.current_stock)
        if movement_type == 'out' and current_stock < quantity:
            return Response({'error': 'Insufficient stock for this movement.'}, status=status.HTTP_400_BAD_REQUEST)

        new_stock = current_stock + quantity if movement_type == 'in' else current_stock - quantity
        product.current_stock = new_stock
        product.stock = new_stock
        update_fields = ['current_stock', 'stock', 'updated_at']
        if movement_type == 'in':
            product.last_restocked = timezone.now().date()
            update_fields.insert(2, 'last_restocked')
        product.save(update_fields=update_fields)

        movement = StockMovement.objects.create(
            product=product,
            type=movement_type,
            quantity=quantity,
            reason=reason,
            current_stock_after=new_stock,
            created_by=request.user,
        )

        return Response(self._serialize_movement(movement), status=status.HTTP_201_CREATED)

    @extend_schema(summary='Inventory alerts', tags=['admin'])
    def alerts(self, request):
        filter_status = request.query_params.get('status', 'active')
        queryset = Product.objects.all().order_by('name')

        low_stock_qs = queryset.filter(current_stock__gt=0, current_stock__lte=models.F('min_stock'))
        out_of_stock_qs = queryset.filter(current_stock__lte=0)

        if filter_status == 'low':
            queryset = low_stock_qs
        elif filter_status == 'out':
            queryset = out_of_stock_qs
        elif filter_status != 'all':
            queryset = low_stock_qs | out_of_stock_qs

        items = [
            {
                'id': str(product.id),
                'name': product.name,
                'sku': product.sku,
                'current_stock': product.current_stock,
                'min_stock': product.min_stock,
                'status': 'out_of_stock' if product.current_stock <= 0 else 'low_stock',
            }
            for product in queryset.distinct()
        ]

        return Response(
            {
                'summary': {
                    'low_stock': low_stock_qs.count(),
                    'out_of_stock': out_of_stock_qs.count(),
                },
                'items': items,
            }
        )

    @extend_schema(summary='Quick restock', tags=['admin'])
    def restock(self, request, product_id=None):
        product = Product.objects.filter(pk=product_id).first()
        if not product:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        quantity = request.data.get('quantity')
        reason = request.data.get('reason', 'Restock')
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return Response({'error': 'Quantity must be a positive integer.'}, status=status.HTTP_400_BAD_REQUEST)

        if quantity <= 0:
            return Response({'error': 'Quantity must be a positive integer.'}, status=status.HTTP_400_BAD_REQUEST)

        product.current_stock = int(product.current_stock) + quantity
        product.stock = product.current_stock
        product.last_restocked = timezone.now().date()
        product.save(update_fields=['current_stock', 'stock', 'last_restocked', 'updated_at'])

        StockMovement.objects.create(
            product=product,
            type='in',
            quantity=quantity,
            reason=reason,
            current_stock_after=product.current_stock,
            created_by=request.user,
        )

        return Response(
            {
                'success': True,
                'product_id': str(product.id),
                'current_stock': product.current_stock,
            }
        )

    @extend_schema(summary='Inventory analytics', tags=['admin'])
    def analytics(self, request):
        last_7_days = timezone.now() - timedelta(days=7)
        recent_movements = StockMovement.objects.filter(date__gte=last_7_days)
        top_products = Product.objects.order_by('-current_stock')[:5]

        return Response(
            {
                'movements_last_7_days': recent_movements.count(),
                'top_stocked_products': [
                    {
                        'id': str(product.id),
                        'name': product.name,
                        'current_stock': product.current_stock,
                    }
                    for product in top_products
                ],
            }
        )

    @extend_schema(summary='Export stock movements CSV', tags=['admin'])
    def export(self, request):
        queryset = StockMovement.objects.select_related('product', 'product__category').order_by('-date')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventory-movements.csv"'

        writer = csv.writer(response)
        writer.writerow(['Date', 'Product', 'Category', 'Type', 'Quantity', 'Reason', 'Stock After'])

        for movement in queryset:
            writer.writerow(
                [
                    timezone.localtime(movement.date).isoformat(),
                    movement.product.name,
                    movement.product.category.name if movement.product.category else '',
                    movement.type,
                    movement.quantity,
                    movement.reason,
                    movement.current_stock_after,
                ]
            )

        return response
