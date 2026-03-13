from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, BasePermission, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from products.models import Product
from sales.models import SalesOrderLine

from .models import Review
from .serializers import ReviewSerializer


class IsReviewOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser or obj.user_id == request.user.id)
        )


class ReviewViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        queryset = Review.objects.select_related('user', 'product').filter(product_id=self.kwargs['product_id'])
        if self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser):
            return queryset
        if self.request.user.is_authenticated:
            return (queryset.filter(is_approved=True) | queryset.filter(user=self.request.user)).distinct()
        return queryset.filter(is_approved=True)

    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny()]
        if self.action == 'approve':
            return [IsAuthenticated(), IsAdminUser()]
        if self.action in {'update', 'partial_update', 'destroy'}:
            return [IsAuthenticated(), IsReviewOwnerOrAdmin()]
        return [IsAuthenticated()]

    def get_object(self):
        review = Review.objects.select_related('user', 'product').filter(
            pk=self.kwargs['review_id'],
            product_id=self.kwargs['product_id'],
        ).first()
        if not review:
            raise NotFound('Review not found.')
        return review

    def list(self, request, *args, **kwargs):
        product = Product.objects.filter(pk=kwargs['product_id']).first()
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        product = Product.objects.filter(pk=kwargs['product_id']).first()
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verified_purchase = SalesOrderLine.objects.filter(
            product=product,
            sales_order__customer__email=request.user.email,
        ).exists()

        review, created = Review.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={
                'rating': serializer.validated_data['rating'],
                'comment': serializer.validated_data.get('comment', ''),
                'verified_purchase': verified_purchase,
                'is_approved': False,
                'approved_at': None,
                'approved_by': None,
            },
        )
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(self.get_serializer(review).data, status=status_code)

    def update(self, request, *args, **kwargs):
        review = self.get_object()
        self.check_object_permissions(request, review)
        partial = kwargs.get('partial', False)
        serializer = self.get_serializer(review, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_review = serializer.save()
        if not request.user.is_staff and not request.user.is_superuser:
            updated_review.is_approved = False
            updated_review.approved_at = None
            updated_review.approved_by = None
            updated_review.save(update_fields=['is_approved', 'approved_at', 'approved_by', 'updated_at'])
        return Response(self.get_serializer(updated_review).data)

    def destroy(self, request, *args, **kwargs):
        review = self.get_object()
        self.check_object_permissions(request, review)
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['patch'], url_path='approve')
    def approve(self, request, *args, **kwargs):
        review = Review.objects.select_related('product').filter(pk=kwargs['pk']).first()
        if not review:
            return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)
        review.is_approved = True
        review.approved_at = timezone.now()
        review.approved_by = request.user
        review.save(update_fields=['is_approved', 'approved_at', 'approved_by', 'updated_at'])
        return Response(ReviewSerializer(review).data)
