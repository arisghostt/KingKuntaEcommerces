from rest_framework.routers import DefaultRouter

from .views import ModuleViewSet, PermissionViewSet, RoleViewSet, UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'roles', RoleViewSet, basename='roles')
router.register(r'permissions', PermissionViewSet, basename='permissions')
router.register(r'modules', ModuleViewSet, basename='modules')

urlpatterns = router.urls
