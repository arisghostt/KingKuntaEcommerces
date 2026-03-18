import logging

from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CustomUser, Module
from .permissions import IsSuperAdmin
from .serializers import (
    CurrentUserSerializer,
    PERMISSION_CATALOG,
    PermissionSerializer,
    RoleSerializer,
    UserSerializer,
    _propagate_role_to_users,
)

logger = logging.getLogger(__name__)


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

    @action(detail=True, methods=['patch'], url_path='reset-password', permission_classes=[IsSuperAdmin])
    def reset_password(self, request, pk=None):
        """
        PATCH /api/users/{id}/reset-password/
        Body: { "new_password": "..." }
        """
        user = self.get_object()
        new_password = request.data.get('new_password') or request.data.get('password')
        if not new_password:
            return Response({'error': 'new_password is required'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save(update_fields=['password'])
        return Response({'success': True}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='assign-role', permission_classes=[IsSuperAdmin])
    def assign_role(self, request, pk=None):
        """
        Assign a role to a user and update their permissions.

        POST /api/users/{id}/assign-role/
        Body: { "role_id": 2 }
        """
        from django.db import transaction
        from .models import RolePermission, UserPermission

        user = self.get_object()
        role_id = request.data.get('role_id')

        if not role_id:
            return Response({'error': 'role_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            role = Group.objects.get(id=role_id)
        except Group.DoesNotExist:
            return Response({'error': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            user.groups.set([role])
            UserPermission.objects.filter(user=user).delete()
            role_perms = RolePermission.objects.filter(role=role).select_related('module')
            if role_perms.exists():
                UserPermission.objects.bulk_create([
                    UserPermission(
                        user=user,
                        module=rp.module,
                        is_view=rp.is_view,
                        is_add=rp.is_add,
                        is_edit=rp.is_edit,
                        is_delete=rp.is_delete,
                    )
                    for rp in role_perms
                ])

            AUTO_ACCESS_MODULES = ['/events', '/chat', '/email', '/settings']
            auto_modules = list(Module.objects.filter(module_url__in=AUTO_ACCESS_MODULES, is_active=True))
            if auto_modules:
                covered = set(
                    UserPermission.objects.filter(user=user).values_list('module__module_url', flat=True)
                )
                missing_auto_modules = [m for m in auto_modules if m.module_url not in covered]
                if missing_auto_modules:
                    UserPermission.objects.bulk_create([
                        UserPermission(
                            user=user,
                            module=m,
                            is_view=True,
                            is_add=False,
                            is_edit=False,
                            is_delete=False,
                        )
                        for m in missing_auto_modules
                    ], ignore_conflicts=True)

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

    def _module_permissions_payload_present(self):
        return bool(self.request.data.get('module_permissions'))

    def _apply_permission_fallback_if_needed(self, group):
        permissions_payload = self.request.data.get('permissions')
        if not permissions_payload or self._module_permissions_payload_present():
            return
        if getattr(self.request, '_role_permissions_fallback_applied', False):
            return

        if isinstance(permissions_payload, str):
            permissions_payload = [permissions_payload]

        codenames = [str(code).strip() for code in permissions_payload if str(code).strip()]
        if not codenames:
            return

        permission_objs = list(Permission.objects.filter(codename__in=codenames))
        missing_codenames = set(codenames) - {perm.codename for perm in permission_objs}

        with transaction.atomic():
            group.permissions.set(permission_objs)

        if missing_codenames:
            logger.warning(
                'RoleViewSet: permissions fallback missing codenames=%s for role=%s',
                ','.join(sorted(missing_codenames)),
                group.name,
            )

        setattr(self.request, '_role_permissions_fallback_applied', True)

    def _maybe_propagate_role(self, instance):
        if not self._module_permissions_payload_present():
            return
        if getattr(self.request, '_role_permissions_propagated', False):
            return
        with transaction.atomic():
            _propagate_role_to_users(instance)
        setattr(self.request, '_role_permissions_propagated', True)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        group_id = response.data.get('id')
        if group_id:
            group = Group.objects.filter(id=group_id).first()
            if group:
                self._apply_permission_fallback_if_needed(group)
                self._maybe_propagate_role(group)
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        instance = self.get_object()
        self._apply_permission_fallback_if_needed(instance)
        self._maybe_propagate_role(instance)
        return response

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        instance = self.get_object()
        self._apply_permission_fallback_if_needed(instance)
        self._maybe_propagate_role(instance)
        return response


class ModuleViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/modules/ — liste tous les modules actifs."""
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Module.objects.filter(is_active=True).order_by('display_order')

    def list(self, request, *args, **kwargs):
        modules = self.get_queryset()
        data = [
            {
                'module_id': m.id,
                'module_name': m.module_name,
                'module_url': m.module_url,
                'is_menu': m.is_menu,
                'is_active': m.is_active,
                'display_order': m.display_order,
            }
            for m in modules
        ]
        return Response(data, status=status.HTTP_200_OK)


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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    module_permissions = user.module_permissions.select_related('module')
    permissions_payload = [
        {
            'module_url': perm.module.module_url,
            'module_name': perm.module.module_name,
            'is_view': perm.is_view,
            'is_add': perm.is_add,
            'is_edit': perm.is_edit,
            'is_delete': perm.is_delete,
        }
        for perm in module_permissions
    ]

    return Response(
        {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'is_superadmin': user.is_superuser,
            'permissions': permissions_payload,
        },
        status=status.HTTP_200_OK,
    )
