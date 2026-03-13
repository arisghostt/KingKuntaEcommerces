from django.contrib.auth.models import Group, Permission
from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CustomUser
from .permissions import IsSuperAdmin
from .serializers import (
    CurrentUserSerializer,
    PERMISSION_CATALOG,
    PermissionSerializer,
    RoleSerializer,
    UserSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.select_related('tenant').all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Enforce IsSuperAdmin for create, update, destroy operations.
        allow-all for GET on /me
        """
        if self.action == 'me':
            return [IsAuthenticated()]
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'assign_role']:
            return [IsSuperAdmin()]
        # List and retrieve are allowed to authenticated users
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'me':
            return CurrentUserSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset()

        role = self.request.query_params.get('role')
        status_param = self.request.query_params.get('status')
        search = self.request.query_params.get('search')

        if role:
            queryset = queryset.filter(groups__name=role)

        if status_param:
            normalized = status_param.strip().lower()
            if normalized == 'active':
                queryset = queryset.filter(is_active=True)
            elif normalized == 'inactive':
                queryset = queryset.filter(is_active=False)

        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) | Q(email__icontains=search)
            )

        return queryset.distinct()

    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def me(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # PATCH: Update allowed fields only
        allowed_fields = {
            'username',
            'email',
            'first_name',
            'last_name',
            'phone',
            'location',
            'bio',
        }
        payload = {key: value for key, value in request.data.items() if key in allowed_fields}
        if 'firstName' in request.data:
            payload['first_name'] = request.data.get('firstName')
        if 'lastName' in request.data:
            payload['last_name'] = request.data.get('lastName')

        serializer = self.get_serializer(request.user, data=payload, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='assign-role', permission_classes=[IsSuperAdmin])
    def assign_role(self, request, pk=None):
        """
        Assign a role to a user and update their permissions.
        
        POST /api/users/{id}/assign-role/
        Body: { "role_id": 2 }
        """
        from django.db import transaction
        from .models import Module, UserPermission, RolePermission

        user = self.get_object()
        role_id = request.data.get('role_id')

        if not role_id:
            return Response(
                {'error': 'role_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            role = Group.objects.get(id=role_id)
        except Group.DoesNotExist:
            return Response(
                {'error': 'Role not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        with transaction.atomic():
            # Update user's groups
            user.groups.set([role])

            # Clear old permissions
            UserPermission.objects.filter(user=user).delete()

            # Propagate role's module permissions to user
            role_perms = RolePermission.objects.filter(role=role).select_related('module')
            UserPermission.objects.bulk_create([
                UserPermission(
                    user=user,
                    module=rp.module,
                    is_view=rp.is_view,
                    is_add=rp.is_add,
                    is_edit=rp.is_edit,
                    is_delete=rp.is_delete,
                    domain_user=user.tenant is not None and user or None
                )
                for rp in role_perms
            ])

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RoleViewSet(viewsets.ModelViewSet):
    queryset = (
        Group.objects.select_related('profile')
        .prefetch_related('permissions')
        .annotate(user_count=Count('user', distinct=True))
        .order_by('id')
    )
    serializer_class = RoleSerializer
    pagination_class = None

    def get_permissions(self):
        """
        Enforce IsSuperAdmin for create, update, destroy operations.
        Allow authenticated users for retrieve and list.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsSuperAdmin()]
        return [IsAuthenticated()]


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    pagination_class = None
    queryset = Permission.objects.none()

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(PERMISSION_CATALOG, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        codename = kwargs.get('pk')
        for item in PERMISSION_CATALOG:
            if item['id'] == codename:
                serializer = self.get_serializer(item)
                return Response(serializer.data, status=status.HTTP_200_OK)
        raise NotFound(detail='Permission not found.')
