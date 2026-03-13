from decimal import Decimal

from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from sales.models import SalesOrder

from .models import Carrier, Shipment, ShippingZone
from .serializers import (
    CarrierSerializer,
    ShipmentSerializer,
    ShippingCalculationResponseSerializer,
    ShippingCalculationSerializer,
    ShippingZoneSerializer,
)


class CarrierViewSet(viewsets.ModelViewSet):
    queryset = Carrier.objects.all()
    serializer_class = CarrierSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class ShippingZoneViewSet(viewsets.ModelViewSet):
    queryset = ShippingZone.objects.all()
    serializer_class = ShippingZoneSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    http_method_names = ['get', 'post', 'head', 'options']


class ShipmentTrackingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        order = SalesOrder.objects.filter(pk=order_id).first()
        if not order:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        shipments = Shipment.objects.filter(order_id=order_id).select_related('carrier', 'zone', 'order')
        payload = {
            'order_id': str(order.id),
            'order_number': order.order_number,
            'order_status': order.status,
            'shipments': ShipmentSerializer(shipments, many=True).data,
        }
        return Response(payload)


class ShippingCostCalculationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ShippingCalculationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        zone = serializer.resolve_zone()
        subtotal = serializer.resolve_subtotal()
        shipping_cost = Decimal('0.00')
        free_shipping_applied = False

        if zone:
            shipping_cost = zone.rate
            if zone.free_shipping_threshold is not None and subtotal >= zone.free_shipping_threshold:
                shipping_cost = Decimal('0.00')
                free_shipping_applied = True

        response_serializer = ShippingCalculationResponseSerializer(
            {
                'zone_id': zone.id if zone else None,
                'zone': zone.name if zone else None,
                'subtotal': subtotal,
                'shipping_cost': shipping_cost,
                'free_shipping_applied': free_shipping_applied,
            }
        )
        return Response(response_serializer.data)
