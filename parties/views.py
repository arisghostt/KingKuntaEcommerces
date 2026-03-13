from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsSuperAdmin

from .serializers import CustomerSerializer, SupplierSerializer


class CustomerListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    @extend_schema(summary='List customers', responses={200: CustomerSerializer(many=True)}, tags=['Parties'])
    def get(self, request):
        from .models import Customer

        customers = Customer.objects.all()
        return Response(CustomerSerializer(customers, many=True).data)

    @extend_schema(
        summary='Create customer',
        request=CustomerSerializer,
        responses={201: CustomerSerializer},
        examples=[OpenApiExample('Customer Example', value={'customer_code': 'CUST-001', 'first_name': 'John', 'last_name': 'Doe', 'email': 'john@example.com'})],
        tags=['Parties'],
    )
    def post(self, request):
        from .models import Customer

        serializer = CustomerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = Customer.objects.create(**serializer.validated_data)
        return Response(CustomerSerializer(customer).data, status=status.HTTP_201_CREATED)


class CustomerDetailView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    @extend_schema(summary='Get customer', responses={200: CustomerSerializer}, tags=['Parties'])
    def get(self, request, pk):
        from .models import Customer

        customer = Customer.objects.filter(pk=pk).first()
        if not customer:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(CustomerSerializer(customer).data)

    @extend_schema(summary='Update customer', request=CustomerSerializer, responses={200: CustomerSerializer}, tags=['Parties'])
    def put(self, request, pk):
        from .models import Customer

        customer = Customer.objects.filter(pk=pk).first()
        if not customer:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CustomerSerializer(customer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for key, value in serializer.validated_data.items():
            setattr(customer, key, value)
        customer.save()
        return Response(CustomerSerializer(customer).data)

    @extend_schema(summary='Delete customer', responses={204: None}, tags=['Parties'])
    def delete(self, request, pk):
        from .models import Customer

        customer = Customer.objects.filter(pk=pk).first()
        if not customer:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
        customer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SupplierListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    @extend_schema(summary='List suppliers', responses={200: SupplierSerializer(many=True)}, tags=['Parties'])
    def get(self, request):
        from .models import Supplier

        suppliers = Supplier.objects.all()
        return Response(SupplierSerializer(suppliers, many=True).data)

    @extend_schema(summary='Create supplier', request=SupplierSerializer, responses={201: SupplierSerializer}, tags=['Parties'])
    def post(self, request):
        from .models import Supplier

        serializer = SupplierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        supplier = Supplier.objects.create(**serializer.validated_data)
        return Response(SupplierSerializer(supplier).data, status=status.HTTP_201_CREATED)


class SupplierDetailView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    @extend_schema(summary='Get supplier', responses={200: SupplierSerializer}, tags=['Parties'])
    def get(self, request, pk):
        from .models import Supplier

        supplier = Supplier.objects.filter(pk=pk).first()
        if not supplier:
            return Response({'error': 'Supplier not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(SupplierSerializer(supplier).data)

    @extend_schema(summary='Update supplier', request=SupplierSerializer, responses={200: SupplierSerializer}, tags=['Parties'])
    def put(self, request, pk):
        from .models import Supplier

        supplier = Supplier.objects.filter(pk=pk).first()
        if not supplier:
            return Response({'error': 'Supplier not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SupplierSerializer(supplier, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for key, value in serializer.validated_data.items():
            setattr(supplier, key, value)
        supplier.save()
        return Response(SupplierSerializer(supplier).data)

    @extend_schema(summary='Delete supplier', responses={204: None}, tags=['Parties'])
    def delete(self, request, pk):
        from .models import Supplier

        supplier = Supplier.objects.filter(pk=pk).first()
        if not supplier:
            return Response({'error': 'Supplier not found'}, status=status.HTTP_404_NOT_FOUND)
        supplier.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
