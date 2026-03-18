from datetime import timedelta

from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsSuperAdmin, IsSuperAdminOrHasModulePermission

from .models import CartItem, Event, Notification
from .serializers import (
    AuthTokenRequestSerializer,
    AuthTokenResponseSerializer,
    AdminNotificationSerializer,
    CartItemSerializer,
    EventSerializer,
    NotificationSerializer,
    WarehouseSerializer,
)

try:
    from sales.models import SalesOrder
except ImportError:  # pragma: no cover - optional dependency
    SalesOrder = None

try:
    from parties.models import Customer
except ImportError:  # pragma: no cover - optional dependency
    Customer = None

try:
    from returns_app.models import ReturnRequest
except ImportError:  # pragma: no cover - optional dependency
    ReturnRequest = None


class AuthRootView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Authentication API root',
        description='Returns links for the auth endpoints.',
        responses={200: OpenApiTypes.OBJECT},
        tags=['auth'],
    )
    def get(self, request):
        return Response(
            {
                'login': request.build_absolute_uri(reverse('token_obtain_pair')),
                'me': request.build_absolute_uri(reverse('auth-me')),
                'refresh': request.build_absolute_uri(reverse('token_refresh')),
                'register': request.build_absolute_uri(reverse('auth-register')),
                'logout': request.build_absolute_uri(reverse('auth-logout')),
            }
        )


class CustomAuthToken(ObtainAuthToken):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Get Bearer Token for API Authentication',
        request=AuthTokenRequestSerializer,
        responses={200: AuthTokenResponseSerializer},
        tags=['auth'],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user_id': user.pk, 'email': user.email})


class AuthStatusView(APIView):
    @extend_schema(summary='Current auth status', responses=AuthTokenResponseSerializer, tags=['auth'])
    def get(self, request):
        if not request.user or not request.user.is_authenticated:
            return Response({'detail': 'Invalid or missing authentication token'}, status=status.HTTP_401_UNAUTHORIZED)

        token, _ = Token.objects.get_or_create(user=request.user)
        return Response({'token': token.key, 'user_id': request.user.pk, 'email': request.user.email})


class EventListCreateView(APIView):
    module_url = '/events'
    permission_classes = [IsAuthenticated, IsSuperAdminOrHasModulePermission]

    @extend_schema(summary='List events', tags=['events'])
    def get(self, request):
        queryset = Event.objects.filter(is_deleted=False).order_by('date', 'created_at')
        search = request.query_params.get('search')
        category = request.query_params.get('category')
        status_filter = request.query_params.get('status')

        if search:
            queryset = queryset.filter(location__icontains=search) | queryset.filter(title__icontains=search)
        if category:
            queryset = queryset.filter(category=category)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        page_number = int(request.query_params.get('page', 1) or 1)
        page_size = int(request.query_params.get('page_size', 10) or 10)
        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)
        serializer = EventSerializer(page.object_list, many=True)

        stats = {
            'total_events': queryset.count(),
            'upcoming_count': queryset.filter(status='upcoming').count(),
            'total_attendees': sum(item.attendees for item in queryset),
            'categories_count': queryset.values('category').distinct().count(),
        }
        return Response(
            {
                'results': serializer.data,
                'total': paginator.count,
                'page': page.number,
                'page_size': page_size,
                'stats': stats,
            }
        )

    @extend_schema(summary='Create event', request=EventSerializer, responses={201: EventSerializer}, tags=['events'])
    def post(self, request):
        serializer = EventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        return Response(EventSerializer(event).data, status=status.HTTP_201_CREATED)


class EventDetailView(APIView):
    module_url = '/events'
    permission_classes = [IsAuthenticated, IsSuperAdminOrHasModulePermission]

    def get_object(self, pk):
        return Event.objects.filter(pk=pk, is_deleted=False).first()

    @extend_schema(summary='Get event', tags=['events'])
    def get(self, request, pk):
        event = self.get_object(pk)
        if not event:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(EventSerializer(event).data)

    @extend_schema(summary='Update event', request=EventSerializer, responses={200: EventSerializer}, tags=['events'])
    def put(self, request, pk):
        event = self.get_object(pk)
        if not event:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = EventSerializer(event, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(summary='Partial update event', request=EventSerializer, responses={200: EventSerializer}, tags=['events'])
    def patch(self, request, pk):
        event = self.get_object(pk)
        if not event:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = EventSerializer(event, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(summary='Delete event', responses={204: None}, tags=['events'])
    def delete(self, request, pk):
        event = self.get_object(pk)
        if not event:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
        event.is_deleted = True
        event.deleted_at = timezone.now()
        event.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary='List notifications', tags=['notifications'])
    def get(self, request):
        queryset = Notification.objects.filter(user=request.user)
        serializer = NotificationSerializer(queryset, many=True)
        return Response(serializer.data)


class AdminNotificationListView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    @extend_schema(summary='List all notifications for admins', tags=['admin'])
    def get(self, request):
        queryset = Notification.objects.select_related('user').order_by('-created_at')

        user_id = request.query_params.get('user_id')
        level = request.query_params.get('level') or request.query_params.get('type')
        is_read = request.query_params.get('is_read')
        search = request.query_params.get('search')

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if level:
            queryset = queryset.filter(level=level)
        if is_read is not None:
            normalized = is_read.strip().lower()
            if normalized in {'true', '1', 'yes'}:
                queryset = queryset.filter(is_read=True)
            elif normalized in {'false', '0', 'no'}:
                queryset = queryset.filter(is_read=False)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(message__icontains=search)
                | Q(user__username__icontains=search)
                | Q(user__email__icontains=search)
            )

        page_number = int(request.query_params.get('page', 1) or 1)
        page_size = int(request.query_params.get('page_size', 20) or 20)
        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)
        serializer = AdminNotificationSerializer(page.object_list, many=True)

        return Response(
            {
                'count': paginator.count,
                'results': serializer.data,
                'page': page.number,
                'page_size': page_size,
            }
        )


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary='Mark notification as read', tags=['notifications'])
    def patch(self, request, pk):
        notification = Notification.objects.filter(pk=pk, user=request.user).first()
        if not notification:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
        notification.mark_as_read()
        return Response(NotificationSerializer(notification).data)


class NotificationDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary='Delete notification', responses={204: None}, tags=['notifications'])
    def delete(self, request, pk):
        notification = Notification.objects.filter(pk=pk, user=request.user).first()
        if not notification:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary='Get current cart', tags=['cart'])
    def get(self, request):
        queryset = CartItem.objects.filter(user=request.user).select_related('product')
        serializer = CartItemSerializer(queryset, many=True)
        return Response({'items': serializer.data, 'count': queryset.count()})


class CartItemCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary='Add item to cart', request=CartItemSerializer, responses={201: CartItemSerializer}, tags=['cart'])
    def post(self, request):
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']
        item, created = CartItem.objects.get_or_create(user=request.user, product=product, defaults={'quantity': quantity})
        if not created:
            item.quantity += quantity
            item.save(update_fields=['quantity', 'updated_at'])
        return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED)


class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary='Update cart item', request=CartItemSerializer, responses={200: CartItemSerializer}, tags=['cart'])
    def put(self, request, pk):
        item = CartItem.objects.filter(pk=pk, user=request.user).select_related('product').first()
        if not item:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)
        quantity = request.data.get('quantity')
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return Response({'error': 'Quantity must be greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)
        if quantity <= 0:
            return Response({'error': 'Quantity must be greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)
        item.quantity = quantity
        item.save(update_fields=['quantity', 'updated_at'])
        return Response(CartItemSerializer(item).data)

    @extend_schema(summary='Remove cart item', responses={204: None}, tags=['cart'])
    def delete(self, request, pk):
        item = CartItem.objects.filter(pk=pk, user=request.user).first()
        if not item:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WarehouseListCreateView(APIView):
    @extend_schema(summary='List warehouses', responses={200: WarehouseSerializer(many=True)}, tags=['Core'])
    def get(self, request):
        from .models import Warehouse

        warehouses = Warehouse.objects.all()
        serializer = WarehouseSerializer(warehouses, many=True)
        return Response(serializer.data)

    @extend_schema(summary='Create warehouse', request=WarehouseSerializer, responses={201: WarehouseSerializer}, tags=['Core'])
    def post(self, request):
        from .models import Warehouse

        serializer = WarehouseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        warehouse = Warehouse.objects.create(**serializer.validated_data)
        return Response(WarehouseSerializer(warehouse).data, status=status.HTTP_201_CREATED)


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary='Dashboard stats', tags=['Core'])
    def get(self, request):
        now = timezone.now()
        last_30 = now - timedelta(days=30)
        prev_30_start = now - timedelta(days=60)

        def safe_sum(queryset, field_name):
            try:
                return queryset.aggregate(total=models.Sum(field_name)).get('total') or 0
            except Exception:
                return 0

        def safe_count(queryset):
            try:
                return queryset.count()
            except Exception:
                return 0

        def percent_change(current, previous):
            try:
                prev_val = float(previous)
                if prev_val:
                    return (float(current) - prev_val) / prev_val * 100
            except Exception:
                pass
            return 0.0

        total_revenue = total_revenue_prev = 0
        total_orders = total_orders_prev = 0
        total_customers = total_customers_prev = 0
        total_refunds = total_refunds_prev = 0

        confirmed_statuses = ['CONFIRMED', 'SHIPPED', 'DELIVERED']
        refund_statuses = ['CANCELLED', 'REFUNDED']

        if SalesOrder:
            try:
                total_revenue = safe_sum(
                    SalesOrder.objects.filter(status__in=confirmed_statuses, created_at__gte=last_30),
                    'total_amount',
                )
                total_revenue_prev = safe_sum(
                    SalesOrder.objects.filter(
                        status__in=confirmed_statuses,
                        created_at__gte=prev_30_start,
                        created_at__lt=last_30,
                    ),
                    'total_amount',
                )
                total_orders = safe_count(SalesOrder.objects.filter(created_at__gte=last_30))
                total_orders_prev = safe_count(
                    SalesOrder.objects.filter(created_at__gte=prev_30_start, created_at__lt=last_30)
                )
                total_refunds = safe_count(
                    SalesOrder.objects.filter(status__in=refund_statuses, created_at__gte=last_30)
                )
                total_refunds_prev = safe_count(
                    SalesOrder.objects.filter(
                        status__in=refund_statuses,
                        created_at__gte=prev_30_start,
                        created_at__lt=last_30,
                    )
                )
            except Exception:
                total_revenue = total_revenue_prev = 0
                total_orders = total_orders_prev = 0
                total_refunds = total_refunds_prev = 0

        if Customer:
            try:
                total_customers = safe_count(Customer.objects.filter(created_at__gte=last_30))
                total_customers_prev = safe_count(
                    Customer.objects.filter(created_at__gte=prev_30_start, created_at__lt=last_30)
                )
            except Exception:
                total_customers = total_customers_prev = 0

        total_revenue_change = percent_change(total_revenue, total_revenue_prev)
        total_orders_change = percent_change(total_orders, total_orders_prev)
        total_customers_change = percent_change(total_customers, total_customers_prev)
        total_refunds_change = percent_change(total_refunds, total_refunds_prev)

        return Response(
            {
                'total_revenue': float(total_revenue),
                'total_revenue_change': total_revenue_change,
                'total_orders': total_orders,
                'total_orders_change': total_orders_change,
                'total_customers': total_customers,
                'total_customers_change': total_customers_change,
                'total_refunds': total_refunds,
                'total_refunds_change': total_refunds_change,
            }
        )


class AdminDashboardStatsView(APIView):
    module_url = '/dashboard'
    permission_classes = [IsAuthenticated, IsSuperAdminOrHasModulePermission]

    @extend_schema(summary='Admin dashboard stats', tags=['admin'])
    def get(self, request):
        now = timezone.now()
        last_30 = now - timedelta(days=30)
        prev_30_start = now - timedelta(days=60)

        def safe_sum(queryset, field_name):
            try:
                return queryset.aggregate(total=models.Sum(field_name)).get('total') or 0
            except Exception:
                return 0

        def safe_count(queryset):
            try:
                return queryset.count()
            except Exception:
                return 0

        total_revenue = total_revenue_prev = 0
        orders_count = orders_prev = 0
        customers_count = 0
        new_customers = new_customers_prev = 0
        refunds_count = refunds_prev = 0
        refunds_amount = 0

        if SalesOrder:
            try:
                total_revenue = safe_sum(
                    SalesOrder.objects.filter(created_at__gte=last_30).exclude(status='CANCELLED'),
                    'total_amount',
                )
                total_revenue_prev = safe_sum(
                    SalesOrder.objects.filter(created_at__gte=prev_30_start, created_at__lt=last_30).exclude(
                        status='CANCELLED'
                    ),
                    'total_amount',
                )
                orders_count = safe_count(SalesOrder.objects.filter(created_at__gte=last_30))
                orders_prev = safe_count(
                    SalesOrder.objects.filter(created_at__gte=prev_30_start, created_at__lt=last_30)
                )
            except Exception:
                total_revenue = total_revenue_prev = 0
                orders_count = orders_prev = 0

        if Customer:
            try:
                customers_count = safe_count(Customer.objects.filter(is_active=True, is_deleted=False))
                new_customers = safe_count(Customer.objects.filter(created_at__gte=last_30))
                new_customers_prev = safe_count(
                    Customer.objects.filter(created_at__gte=prev_30_start, created_at__lt=last_30)
                )
            except Exception:
                customers_count = new_customers = new_customers_prev = 0

        if ReturnRequest:
            try:
                refunds_queryset = ReturnRequest.objects.filter(status='refunded', created_at__gte=last_30)
                refunds_count = safe_count(refunds_queryset)
                refunds_amount = safe_sum(refunds_queryset, 'refund_amount')
                refunds_prev = safe_count(
                    ReturnRequest.objects.filter(
                        status='refunded',
                        created_at__gte=prev_30_start,
                        created_at__lt=last_30,
                    )
                )
            except Exception:
                refunds_count = refunds_prev = refunds_amount = 0

        return Response(
            {
                'total_revenue': float(total_revenue),
                'total_revenue_change': float(total_revenue - total_revenue_prev),
                'orders_count': orders_count,
                'orders_change': orders_count - orders_prev,
                'customers_count': customers_count,
                'customers_change': new_customers - new_customers_prev,
                'refunds_count': refunds_count,
                'refunds_amount': float(refunds_amount),
                'refunds_change': refunds_count - refunds_prev,
            }
        )
