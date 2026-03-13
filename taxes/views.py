from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from .models import Tax
from .serializers import TaxSerializer


class TaxViewSet(viewsets.ModelViewSet):
    queryset = Tax.objects.prefetch_related('applicable_products', 'applicable_categories')
    serializer_class = TaxSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

