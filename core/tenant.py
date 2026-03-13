from rest_framework.exceptions import PermissionDenied


class TenantScopedQuerysetMixin:
    """
    Reusable queryset scoping for models that carry a `tenant_id` column.
    """

    tenant_field = 'tenant'
    allow_superuser_unscoped = True
    require_tenant = True

    def get_request_tenant(self):
        user = getattr(self.request, 'user', None)
        if not user or not user.is_authenticated:
            return None
        return getattr(user, 'tenant', None)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.allow_superuser_unscoped and getattr(self.request.user, 'is_superuser', False):
            return queryset

        tenant = self.get_request_tenant()
        if tenant is None:
            if self.require_tenant:
                return queryset.none()
            return queryset

        tenant_field = f'{self.tenant_field}_id'
        if hasattr(queryset.model, tenant_field):
            return queryset.filter(**{tenant_field: tenant.id})
        return queryset


class TenantAssignOnCreateMixin:
    """
    Automatically assigns the current user's tenant on create.
    """

    tenant_field = 'tenant'
    allow_superuser_without_tenant = False

    def perform_create(self, serializer):
        user = getattr(self.request, 'user', None)
        tenant = getattr(user, 'tenant', None) if user and user.is_authenticated else None

        if tenant is None and not (self.allow_superuser_without_tenant and getattr(user, 'is_superuser', False)):
            raise PermissionDenied('A tenant is required to create this resource.')

        if tenant is None:
            serializer.save()
            return

        serializer.save(**{self.tenant_field: tenant})
