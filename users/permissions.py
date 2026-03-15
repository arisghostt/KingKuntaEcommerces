from rest_framework.permissions import BasePermission

from .models import UserPermission


class IsSuperAdmin(BasePermission):
    """Accès réservé aux superadmins uniquement (inchangé)."""
    message = "Accès réservé au superadmin."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superadmin


class HasModulePermission(BasePermission):
    """
    Vérifie que l'utilisateur a la permission 'action' sur le module 'module_url'.
    Usage sur une vue :
        permission_classes = [IsAuthenticated, HasModulePermission]
        module_url = '/customers'
        required_action = 'is_view'  # ou is_add, is_edit, is_delete
    """
    message = "Vous n'avez pas les permissions requises pour ce module."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superadmin:
            return True

        module_url = getattr(view, 'module_url', None)
        if not module_url:
            return False

        method = request.method.upper()
        if method == 'GET':
            action = getattr(view, 'required_action', 'is_view')
        elif method == 'POST':
            action = 'is_add'
        elif method in ('PUT', 'PATCH'):
            action = 'is_edit'
        elif method == 'DELETE':
            action = 'is_delete'
        else:
            action = 'is_view'

        return UserPermission.objects.select_related('module').filter(
            user=request.user,
            module__module_url=module_url,
            **{action: True}
        ).exists()


class IsSuperAdminOrHasModulePermission(BasePermission):
    """
    Accès si superadmin OU si UserPermission valide pour le module.
    C'est la permission principale à utiliser sur toutes les vues admin.
    """
    message = "Accès non autorisé."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superadmin:
            return True

        module_url = getattr(view, 'module_url', None)
        if not module_url:
            return False

        method = request.method.upper()
        if method == 'GET':
            action = 'is_view'
        elif method == 'POST':
            action = 'is_add'
        elif method in ('PUT', 'PATCH'):
            action = 'is_edit'
        elif method == 'DELETE':
            action = 'is_delete'
        else:
            action = 'is_view'

        return UserPermission.objects.select_related('module').filter(
            user=request.user,
            module__module_url=module_url,
            **{action: True}
        ).exists()
