from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Sum, Count

from .models import Coupon

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_coupons_list(request):
    """List coupons with filtering by status and type"""
    status_filter = request.query_params.get('status', 'all')
    type_filter = request.query_params.get('type', 'all')
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    
    queryset = Coupon.objects.prefetch_related('applicable_products')
    
    # Filter by type
    if type_filter != 'all':
        queryset = queryset.filter(type=type_filter)
    
    # Filter by status
    now = timezone.now()
    if status_filter == 'active':
        queryset = queryset.filter(is_active=True, date_expiry__gt=now)
    elif status_filter == 'expired':
        queryset = queryset.filter(date_expiry__lte=now)
    elif status_filter == 'disabled':
        queryset = queryset.filter(is_active=False)
    
    # Calculate stats
    all_coupons = Coupon.objects.all()
    total_coupons = all_coupons.count()
    active_count = all_coupons.filter(is_active=True, date_expiry__gt=now).count()
    scheduled_count = all_coupons.filter(is_active=True, date_expiry__gt=now + timedelta(days=30)).count()
    expired_count = all_coupons.filter(date_expiry__lte=now).count()
    
    # Get total discounts (estimated based on value and usage_count)
    total_discounts = sum([
        float(c.value) * c.usage_count 
        for c in all_coupons if c.type == 'fixed'
    ])
    
    stats = {
        'total': total_coupons,
        'active': active_count,
        'scheduled': scheduled_count,
        'expired': expired_count,
        'total_discounts_given': total_discounts,
    }
    
    # Paginate
    total_count = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size
    coupons = queryset[start:end]
    
    # Serialize
    coupon_list = []
    for coupon in coupons:
        if coupon.date_expiry <= now:
            coupon_status = 'expired'
        elif not coupon.is_active:
            coupon_status = 'disabled'
        else:
            coupon_status = 'active'
        
        coupon_data = {
            'id': coupon.id,
            'code': coupon.code,
            'type': coupon.type,
            'value': float(coupon.value),
            'min_order_amount': float(coupon.min_order_amount),
            'max_discount_amount': None,
            'start_date': coupon.created_at.isoformat() if coupon.created_at else None,
            'end_date': coupon.date_expiry.isoformat() if coupon.date_expiry else None,
            'usage_limit': coupon.usage_limit,
            'usage_limit_per_user': None,
            'used_count': coupon.usage_count,
            'is_active': coupon.is_active,
            'applicable_to': 'product' if coupon.applicable_products.exists() else 'all',
            'applicable_categories': [],
            'applicable_products': [
                {'id': p.id, 'name': p.name}
                for p in coupon.applicable_products.all()
            ],
            'status': coupon_status,
            'created_at': coupon.created_at.isoformat() if coupon.created_at else None,
        }
        coupon_list.append(coupon_data)
    
    return Response({
        'stats': stats,
        'results': coupon_list,
        'count': total_count,
        'page': page,
        'page_size': page_size,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_coupons_analytics(request):
    """Get coupon analytics"""
    period = request.query_params.get('period', '30d')
    
    # Parse period
    if period.endswith('d'):
        days = int(period[:-1])
    else:
        days = 30
    
    start_date = timezone.now() - timedelta(days=days)
    
    # Get coupons used in the period
    coupons = Coupon.objects.filter(created_at__gte=start_date)
    
    # Usage over time (simplified - using creation date)
    usage_over_time = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        day_coupons = coupons.filter(
            created_at__date=date.date()
        )
        total_discount = sum([
            float(c.value) * c.usage_count
            for c in day_coupons if c.type == 'fixed'
        ])
        usage_over_time.append({
            'date': date.isoformat(),
            'usages_count': sum([c.usage_count for c in day_coupons]),
            'total_discount_amount': total_discount,
        })
    
    # Top coupons
    top_coupons_qs = Coupon.objects.all().order_by('-usage_count')[:5]
    top_coupons = []
    for coupon in top_coupons_qs:
        total_discount = float(coupon.value) * coupon.usage_count if coupon.type == 'fixed' else 0
        top_coupons.append({
            'code': coupon.code,
            'used_count': coupon.usage_count,
            'total_discount_given': total_discount,
            'revenue_generated': 0,  # Would need order data
        })
    
    # Discount by type
    discount_by_type = []
    for type_choice, type_label in Coupon.TYPE_CHOICES:
        type_coupons = Coupon.objects.filter(type=type_choice)
        count = type_coupons.count()
        total_amount = sum([
            float(c.value) * c.usage_count
            for c in type_coupons if c.type == 'fixed'
        ])
        discount_by_type.append({
            'type': type_label,
            'count': count,
            'total_amount': total_amount,
        })
    
    return Response({
        'usage_over_time': usage_over_time,
        'top_coupons': top_coupons,
        'discount_by_type': discount_by_type,
    })


urlpatterns = [
    path('coupons/', admin_coupons_list, name='admin-coupons-list'),
    path('coupons/analytics/', admin_coupons_analytics, name='admin-coupons-analytics'),
]
