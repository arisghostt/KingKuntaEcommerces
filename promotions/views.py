from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import Coupon, Promotion
from .serializers import (
    CouponSerializer,
    CouponValidationResponseSerializer,
    CouponValidationSerializer,
    PromotionSerializer,
)


class PromotionViewSet(viewsets.ModelViewSet):
    queryset = Promotion.objects.prefetch_related('applicable_products')
    serializer_class = PromotionSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.prefetch_related('applicable_products')
    serializer_class = CouponSerializer

    def get_permissions(self):
        if self.action == 'validate_coupon':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    @action(detail=False, methods=['post'], url_path='validate')
    def validate_coupon(self, request):
        serializer = CouponValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        coupon = Coupon.objects.filter(code=serializer.validated_data['code']).first()
        if not coupon:
            payload = CouponValidationResponseSerializer.build(None, serializer.validated_data['order_amount'], 'Coupon not found.')
            return Response(payload, status=status.HTTP_404_NOT_FOUND)

        order_amount = serializer.validated_data['order_amount']
        product_ids = serializer.validated_data.get('product_ids') or []

        if not coupon.is_usable(order_amount):
            payload = CouponValidationResponseSerializer.build(coupon, order_amount, 'Coupon is not valid for this order.')
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        if product_ids:
            applicable_ids = set(coupon.applicable_products.values_list('id', flat=True))
            if applicable_ids and not applicable_ids.intersection(product_ids):
                payload = CouponValidationResponseSerializer.build(coupon, order_amount, 'Coupon does not apply to the selected products.')
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        payload = CouponValidationResponseSerializer.build(coupon, order_amount)
        return Response(payload)

