from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    message = "Accès réservé au superadmin."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superadmin

