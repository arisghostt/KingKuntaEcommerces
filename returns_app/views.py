from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import ReturnRequest
from .serializers import ReturnRequestSerializer


class ReturnRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ReturnRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ReturnRequest.objects.select_related('order', 'requester', 'reviewed_by')
        if self.request.user.is_staff or self.request.user.is_superuser:
            return queryset
        return queryset.filter(requester=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.validated_data['order']
        if not (request.user.is_staff or request.user.is_superuser) and order.customer.email != request.user.email:
            return Response({'error': 'You can only create returns for your own orders.'}, status=status.HTTP_403_FORBIDDEN)
        return_request = serializer.save(requester=request.user)
        return Response(self.get_serializer(return_request).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not (request.user.is_staff or request.user.is_superuser or instance.requester_id == request.user.id):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        if not (request.user.is_staff or request.user.is_superuser):
            serializer.validated_data['status'] = instance.status
            serializer.validated_data['refund_amount'] = instance.refund_amount
            serializer.validated_data['admin_notes'] = instance.admin_notes
        updated_instance = serializer.save()
        return Response(self.get_serializer(updated_instance).data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsAdminUser])
    def approve(self, request, pk=None):
        return_request = self.get_queryset().filter(pk=pk).first()
        if not return_request:
            return Response({'error': 'Return request not found'}, status=status.HTTP_404_NOT_FOUND)
        return_request.status = 'approved'
        return_request.reviewed_at = timezone.now()
        return_request.reviewed_by = request.user
        return_request.save(update_fields=['status', 'reviewed_at', 'reviewed_by', 'updated_at'])
        return Response(self.get_serializer(return_request).data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsAdminUser])
    def reject(self, request, pk=None):
        return_request = self.get_queryset().filter(pk=pk).first()
        if not return_request:
            return Response({'error': 'Return request not found'}, status=status.HTTP_404_NOT_FOUND)
        return_request.status = 'rejected'
        return_request.admin_notes = request.data.get('admin_notes', return_request.admin_notes)
        return_request.reviewed_at = timezone.now()
        return_request.reviewed_by = request.user
        return_request.save(update_fields=['status', 'admin_notes', 'reviewed_at', 'reviewed_by', 'updated_at'])
        return Response(self.get_serializer(return_request).data)
