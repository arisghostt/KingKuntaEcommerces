import logging

from django.contrib.auth.models import Group, Permission
from django.db import transaction
from rest_framework import serializers

from core.models import Tenant

from .models import CustomUser, Module, RolePermission, RoleProfile, UserPermission

logger = logging.getLogger(__name__)


def _build_permissions_for_user(user):
    """Retourne la liste des modules actifs avec les flags de permission pour un utilisateur."""
    modules = Module.objects.filter(is_active=True, is_menu=True).order_by('display_order')
    if user.is_superadmin:
        return [
            {
                'module_id': m.id,
                'module_name': m.module_name,
                'module_url': m.module_url,
                'is_menu': m.is_menu,
                'is_active': m.is_active,
                'display_order': m.display_order,
                'is_view': True,
                'is_add': True,
                'is_edit': True,
                'is_delete': True,
            }
            for m in modules
        ]
    user_perms = {p.module_id: p for p in UserPermission.objects.filter(user=user)}
    return [
        {
            'module_id': m.id,
            'module_name': m.module_name,
            'module_url': m.module_url,
            'is_menu': m.is_menu,
            'is_active': m.is_active,
            'display_order': m.display_order,
            'is_view': user_perms[m.id].is_view if m.id in user_perms else False,
            'is_add': user_perms[m.id].is_add if m.id in user_perms else False,
            'is_edit': user_perms[m.id].is_edit if m.id in user_perms else False,
            'is_delete': user_perms[m.id].is_delete if m.id in user_perms else False,
        }
        for m in modules
    ]


def _propagate_role_to_users(group):
    """Re-propage les RolePermission d'un rôle vers tous ses utilisateurs."""
    role_perms = list(RolePermission.objects.filter(role=group).select_related('module'))
    users = CustomUser.objects.filter(groups=group)
    for user in users:
        UserPermission.objects.filter(user=user).delete()
        if role_perms:
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


PERMISSION_CATALOG = [
    {
        'id': 'dashboard_view',
        'name': 'View Dashboard',
        'description': 'Access to dashboard overview',
        'category': 'Dashboard',
    },
    {
        'id': 'dashboard_analytics',
        'name': 'View Analytics',
        'description': 'Access to analytics data',
        'category': 'Dashboard',
    },
    {
        'id': 'products_view',
        'name': 'View Products',
        'description': 'View product list',
        'category': 'Products',
    },
    {
        'id': 'products_add',
        'name': 'Add Products',
        'description': 'Create new products',
        'category': 'Products',
    },
    {
        'id': 'products_edit',
        'name': 'Edit Products',
        'description': 'Modify existing products',
        'category': 'Products',
    },
    {
        'id': 'products_delete',
        'name': 'Delete Products',
        'description': 'Remove products',
        'category': 'Products',
    },
    {
        'id': 'orders_view',
        'name': 'View Orders',
        'description': 'View order list',
        'category': 'Orders',
    },
    {
        'id': 'orders_edit',
        'name': 'Edit Orders',
        'description': 'Modify order status',
        'category': 'Orders',
    },
    {
        'id': 'customers_view',
        'name': 'View Customers',
        'description': 'View customer list',
        'category': 'Customers',
    },
    {
        'id': 'customers_edit',
        'name': 'Edit Customers',
        'description': 'Modify customer data',
        'category': 'Customers',
    },
    {
        'id': 'users_view',
        'name': 'View Users',
        'description': 'View user list',
        'category': 'Users',
    },
    {
        'id': 'users_create',
        'name': 'Create Users',
        'description': 'Add new users',
        'category': 'Users',
    },
    {
        'id': 'users_edit',
        'name': 'Edit Users',
        'description': 'Modify user accounts',
        'category': 'Users',
    },
    {
        'id': 'users_roles',
        'name': 'Manage Roles',
        'description': 'Assign and modify user roles',
        'category': 'Users',
    },
    {
        'id': 'billing_view',
        'name': 'View Billing',
        'description': 'Access billing information',
        'category': 'Billing',
    },
    {
        'id': 'billing_manage',
        'name': 'Manage Billing',
        'description': 'Manage billing settings',
        'category': 'Billing',
    },
]


class PermissionSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    category = serializers.CharField()


class RolePermissionInputSerializer(serializers.Serializer):
    module_id = serializers.IntegerField()
    is_view = serializers.BooleanField(default=False)
    is_add = serializers.BooleanField(default=False)
    is_edit = serializers.BooleanField(default=False)
    is_delete = serializers.BooleanField(default=False)


class RoleSerializer(serializers.ModelSerializer):
    module_permissions = serializers.ListField(
        child=RolePermissionInputSerializer(),
        write_only=True,
        required=False,
        allow_empty=True,
    )
    permissions = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        allow_empty=True,
    )
    description = serializers.CharField(write_only=True, required=False, allow_blank=True)
    color = serializers.CharField(write_only=True, required=False, max_length=30)
    userCount = serializers.SerializerMethodField(read_only=True)
    module_permissions_read = serializers.SerializerMethodField(read_only=True, source='*')

    class Meta:
        model = Group
        fields = [
        'id',
        'name',
        'description',
        'module_permissions',
        'permissions',
        'userCount',
        'color',
        'module_permissions_read',
        ]
        read_only_fields = ['id', 'userCount', 'module_permissions_read']

    def get_userCount(self, obj):
        annotated_count = getattr(obj, 'user_count', None)
        if annotated_count is not None:
            return annotated_count
        return obj.user_set.count()

    def get_module_permissions_read(self, obj):
        """
        Get list of modules with permissions assigned to this role.
        Returns list of modules the role can access with specific actions.
        """
        from .models import Module, RolePermission

        modules = Module.objects.filter(is_active=True).order_by('display_order')
        role_perms = {rp.module_id: rp for rp in RolePermission.objects.filter(role=obj)}
        
        return [
            {
                'module_id': m.id,
                'module_name': m.module_name,
                'module_url': m.module_url,
                'is_view': role_perms[m.id].is_view if m.id in role_perms else False,
                'is_add': role_perms[m.id].is_add if m.id in role_perms else False,
                'is_edit': role_perms[m.id].is_edit if m.id in role_perms else False,
                'is_delete': role_perms[m.id].is_delete if m.id in role_perms else False,
            }
            for m in modules
        ]

    def _save_role_permissions(self, group, module_permissions):
        """Save module permissions for a role, replacing existing ones."""
        from .models import Module, RolePermission
        
        if not module_permissions:
            return
        
        # Delete existing permissions
        RolePermission.objects.filter(role=group).delete()
        
        # Collect module IDs for validation
        module_ids = [mp['module_id'] for mp in module_permissions]
        modules = {m.id: m for m in Module.objects.filter(id__in=module_ids)}
        missing_module_ids = set(module_ids) - set(modules.keys())
        for missing_module_id in sorted(missing_module_ids):
            logger.warning(
                "RolePermission: module_id=%s introuvable pour rôle %s",
                missing_module_id,
                group.name,
            )
        
        # Create new permissions
        perms_to_create = []
        for mp in module_permissions:
            module_id = mp['module_id']
            if module_id in modules:
                perms_to_create.append(
                    RolePermission(
                        role=group,
                        module=modules[module_id],
                        is_view=mp.get('is_view', False),
                        is_add=mp.get('is_add', False),
                        is_edit=mp.get('is_edit', False),
                        is_delete=mp.get('is_delete', False),
                    )
                )
        
        RolePermission.objects.bulk_create(perms_to_create)

    def _save_profile(self, group, description, color):
        profile, _ = RoleProfile.objects.get_or_create(group=group)
        profile.description = description
        profile.color = color
        profile.save(update_fields=['description', 'color'])

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop('permissions', [])
        module_permissions = validated_data.pop('module_permissions', [])
        description = validated_data.pop('description', '')
        color = validated_data.pop('color', RoleProfile._meta.get_field('color').default)

        group = Group.objects.create(**validated_data)
        self._save_profile(group, description, color)
        self._save_role_permissions(group, module_permissions)

        return group

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data.pop('permissions', serializers.empty)
        module_permissions = validated_data.pop('module_permissions', serializers.empty)
        description = validated_data.pop('description', serializers.empty)
        color = validated_data.pop('color', serializers.empty)

        instance.name = validated_data.get('name', instance.name)
        instance.save(update_fields=['name'])

        profile, _ = RoleProfile.objects.get_or_create(group=instance)
        profile_changed = False

        if description is not serializers.empty:
            profile.description = description
            profile_changed = True
        if color is not serializers.empty:
            profile.color = color
            profile_changed = True
        if profile_changed:
            profile.save(update_fields=['description', 'color'])

        if module_permissions is not serializers.empty:
            self._save_role_permissions(instance, module_permissions)
            _propagate_role_to_users(instance)
            request = self.context.get('request')
            if request:
                setattr(request, '_role_permissions_propagated', True)

        return instance

    def to_representation(self, instance):
        payload = super().to_representation(instance)
        profile = getattr(instance, 'profile', None)

        payload['description'] = profile.description if profile else ''
        payload['color'] = (
            profile.color if profile else RoleProfile._meta.get_field('color').default
        )

        return payload


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField(read_only=True)
    role_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    tenant_id = serializers.PrimaryKeyRelatedField(source='tenant', queryset=Tenant.objects.all(), required=False, allow_null=True)
    tenant = serializers.SerializerMethodField(read_only=True)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'phone',
            'location',
            'bio',
            'tenant',
            'tenant_id',
            'role',
            'role_id',
            'is_active',
            'date_joined',
            'last_login',
            'password',
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'role']

    def _resolve_group(self, role_id):
        try:
            return Group.objects.get(id=role_id)
        except Group.DoesNotExist as exc:
            raise serializers.ValidationError({'role_id': 'Invalid role_id.'}) from exc

    def get_role(self, obj):
        group = obj.groups.order_by('id').first()
        if not group:
            return None
        return {'id': group.id, 'name': group.name}

    def get_tenant(self, obj):
        if not obj.tenant_id:
            return None
        return {'id': obj.tenant_id, 'name': obj.tenant.name}

    def create(self, validated_data):
        role_id = validated_data.pop('role_id', None)
        password = validated_data.pop('password', None)

        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()

        if role_id is not None:
            group = self._resolve_group(role_id)
            user.groups.set([group])

        return user

    def update(self, instance, validated_data):
        role_id = validated_data.pop('role_id', serializers.empty)
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        if role_id is not serializers.empty:
            if role_id is None:
                instance.groups.set([])
            else:
                group = self._resolve_group(role_id)
                instance.groups.set([group])

        return instance


class CurrentUserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField(read_only=True)
    tenant = serializers.SerializerMethodField(read_only=True)
    is_superadmin = serializers.SerializerMethodField(read_only=True)
    permissions = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'phone',
            'location',
            'bio',
            'tenant',
            'role',
            'is_superadmin',
            'permissions',
            'date_joined',
            'last_login',
        ]
        read_only_fields = ['id', 'role', 'is_superadmin', 'permissions', 'date_joined', 'last_login']

    def get_role(self, obj):
        group = obj.groups.order_by('id').first()
        if not group:
            return None
        return {'id': group.id, 'name': group.name}

    def get_tenant(self, obj):
        if not obj.tenant_id:
            return None
        return {'id': obj.tenant_id, 'name': obj.tenant.name}

    def get_is_superadmin(self, obj):
        return obj.is_superadmin

    def get_permissions(self, obj):
        return _build_permissions_for_user(obj)
