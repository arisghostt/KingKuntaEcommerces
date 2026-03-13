import uuid

from django.db.models import Q
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import Category, Product
from products.serializers import CategorySerializer, ProductSerializer

from .models import SearchQueryLog
from .serializers import SearchResultSerializer


class SearchView(APIView):
    permission_classes = [AllowAny]
    search_fields = ['name', 'description', 'sku']

    @staticmethod
    def _maybe_uuid(value):
        try:
            return uuid.UUID(str(value))
        except (TypeError, ValueError, AttributeError):
            return None

    def get(self, request):
        product_queryset = Product.objects.select_related('category').prefetch_related('gallery_images', 'variants')
        category_queryset = Category.objects.all()

        category_filter = request.query_params.get('category')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        in_stock = request.query_params.get('in_stock')

        product_queryset = SearchFilter().filter_queryset(request, product_queryset, self)

        q_value = (request.query_params.get('q') or '').strip()
        if q_value:
            category_queryset = category_queryset.filter(Q(name__icontains=q_value) | Q(description__icontains=q_value))

        if category_filter:
            category_uuid = self._maybe_uuid(category_filter)
            product_filters = Q(category__name__icontains=category_filter)
            category_filters = Q(name__icontains=category_filter)
            if category_uuid:
                product_filters |= Q(category__id=category_uuid)
                category_filters |= Q(id=category_uuid)
            product_queryset = product_queryset.filter(product_filters)
            category_queryset = category_queryset.filter(category_filters)
        if min_price:
            product_queryset = product_queryset.filter(price__gte=min_price)
        if max_price:
            product_queryset = product_queryset.filter(price__lte=max_price)
        if in_stock is not None and in_stock != '':
            normalized = in_stock.strip().lower()
            if normalized in {'true', '1', 'yes'}:
                product_queryset = product_queryset.filter(current_stock__gt=0)
            elif normalized in {'false', '0', 'no'}:
                product_queryset = product_queryset.filter(current_stock__lte=0)

        products = product_queryset.distinct()
        categories = category_queryset.distinct()
        payload = {
            'products': ProductSerializer(products, many=True, context={'request': request}).data,
            'categories': CategorySerializer(categories, many=True).data,
            'count': products.count() + categories.count(),
        }

        SearchQueryLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            query=q_value,
            filters={
                'category': category_filter,
                'min_price': min_price,
                'max_price': max_price,
                'in_stock': in_stock,
            },
            result_count=payload['count'],
        )

        serializer = SearchResultSerializer(payload)
        return Response(serializer.data)
