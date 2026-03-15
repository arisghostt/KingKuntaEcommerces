import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db import DatabaseError, OperationalError
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.serializers import RegisterSerializer

logger = logging.getLogger(__name__)


def _resolve_user_role(user):
    if getattr(user, 'is_superuser', False):
        return 'superadmin'
    if getattr(user, 'is_staff', False):
        return 'admin'
    first_group = user.groups.order_by('id').first()
    if first_group:
        return first_group.name
    return 'user'


def _get_user_permissions(user):
    from users.models import Module, UserPermission

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


def _get_role_permissions(group, is_superadmin):
    if is_superadmin:
        from users.models import Module

        modules = Module.objects.filter(is_active=True).order_by('display_order')
        return [
            {
                'module_id': m.id,
                'module_name': m.module_name,
                'module_url': m.module_url,
                'is_view': True,
                'is_add': True,
                'is_edit': True,
                'is_delete': True,
            }
            for m in modules
        ]

    if not group:
        return []

    from users.models import RolePermission

    role_perms = (
        RolePermission.objects.filter(role=group)
        .select_related('module')
        .order_by('module__display_order')
    )
    return [
        {
            'module_id': rp.module_id,
            'module_name': rp.module.module_name,
            'module_url': rp.module.module_url,
            'is_view': rp.is_view,
            'is_add': rp.is_add,
            'is_edit': rp.is_edit,
            'is_delete': rp.is_delete,
        }
        for rp in role_perms
    ]


def _build_role_payload(user, group):
    is_superadmin = getattr(user, 'is_superadmin', False)
    role_id = group.id if group else 0
    return {
        'id': role_id or 0,
        'name': _resolve_user_role(user),
        'permissions': _get_role_permissions(group, is_superadmin),
    }


def _serialize_user_for_auth_response(user, request):
    group = user.groups.order_by('id').first()
    role_payload = _build_role_payload(user, group)
    return {
        'id': user.pk,
        'user_id': user.pk,
        'username': user.get_username(),
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone': getattr(user, 'phone', ''),
        'location': getattr(user, 'location', ''),
        'bio': getattr(user, 'bio', ''),
        'tenant_id': getattr(user, 'tenant_id', None),
        'tenant_name': getattr(getattr(user, 'tenant', None), 'name', None),
        'role_id': group.id if group else None,
        'role': role_payload,
        'is_superadmin': getattr(user, 'is_superadmin', False),
        'permissions': _get_user_permissions(user),
    }


class SafeTokenObtainPairView(TokenObtainPairView):
    @extend_schema(tags=['auth'])
    def post(self, request, *args, **kwargs):
        try:
            payload = request.data.copy()
            identifier = (
                payload.get('username')
                or payload.get('email')
                or payload.get('identifier')
                or payload.get('login')
                or payload.get('user')
            )

            if identifier:
                identifier = str(identifier).strip()
                if '@' in identifier:
                    user = get_user_model().objects.filter(email__iexact=identifier).only('username').first()
                    payload['username'] = user.username if user else identifier
                elif not payload.get('username'):
                    payload['username'] = identifier

            serializer = self.get_serializer(data=payload)
            serializer.is_valid(raise_exception=True)
            access_token = serializer.validated_data.get('access')
            refresh_token = serializer.validated_data.get('refresh')
            response_payload = {}
            if access_token:
                response_payload['access'] = str(access_token)
            if refresh_token:
                response_payload['refresh'] = str(refresh_token)
            if getattr(serializer, 'user', None) is not None:
                response_payload['user'] = _serialize_user_for_auth_response(serializer.user, request)
            response = Response(response_payload, status=status.HTTP_200_OK)
            secure_cookie = not settings.DEBUG

            if access_token:
                response.set_cookie('access_token', str(access_token), httponly=True, secure=secure_cookie, samesite='Lax', path='/')
            if refresh_token:
                response.set_cookie('refresh_token', str(refresh_token), httponly=True, secure=secure_cookie, samesite='Lax', path='/')
            return response
        except TokenError as exc:
            raise InvalidToken(exc.args[0]) from exc
        except ValidationError:
            raise
        except (OperationalError, DatabaseError):
            logger.exception('Database error during JWT login')
            return Response({'detail': 'Authentication service temporarily unavailable. Please retry.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class SafeTokenRefreshView(TokenRefreshView):
    @extend_schema(tags=['auth'])
    def post(self, request, *args, **kwargs):
        try:
            payload = request.data.copy()
            if not payload.get('refresh'):
                refresh_from_cookie = request.COOKIES.get('refresh_token', '').strip()
                if refresh_from_cookie:
                    payload['refresh'] = refresh_from_cookie.replace('Bearer ', '').replace('Token ', '').strip()

            serializer = self.get_serializer(data=payload)
            serializer.is_valid(raise_exception=True)
            response_payload = dict(serializer.validated_data)
            response = Response(response_payload, status=status.HTTP_200_OK)

            secure_cookie = not settings.DEBUG
            access_token = serializer.validated_data.get('access')
            refresh_token = serializer.validated_data.get('refresh')
            if access_token:
                response.set_cookie('access_token', str(access_token), httponly=True, secure=secure_cookie, samesite='Lax', path='/')
            if refresh_token:
                response.set_cookie('refresh_token', str(refresh_token), httponly=True, secure=secure_cookie, samesite='Lax', path='/')
            return response
        except TokenError as exc:
            raise InvalidToken(exc.args[0]) from exc
        except ValidationError:
            raise
        except (OperationalError, DatabaseError):
            logger.exception('Database error during JWT refresh')
            return Response({'detail': 'Authentication service temporarily unavailable. Please retry.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(tags=['auth'])
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                'id': user.pk,
                'username': user.username,
                'email': user.email,
                'tenant_id': getattr(user, 'tenant_id', None),
            },
            status=status.HTTP_201_CREATED,
        )


class LogoutView(APIView):
    @extend_schema(tags=['auth'])
    def post(self, request):
        response = Response({'success': True}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')
        return response


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=['auth'])
    def get(self, request):
        user_payload = _serialize_user_for_auth_response(request.user, request)
        response_payload = dict(user_payload)
        response_payload['user'] = user_payload
        return Response(response_payload, status=status.HTTP_200_OK)


class PasswordResetView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(tags=['auth'])
    def post(self, request):
        email = str(request.data.get('email', '')).strip().lower()
        user = get_user_model().objects.filter(email__iexact=email).first()
        payload = {'detail': 'If the email exists, a reset token has been generated.'}
        if user:
            payload['uid'] = urlsafe_base64_encode(force_bytes(user.pk))
            payload['token'] = default_token_generator.make_token(user)
        return Response(payload, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(tags=['auth'])
    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        password = request.data.get('password') or request.data.get('new_password')
        if not uid or not token or not password:
            return Response({'error': 'uid, token and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = get_user_model().objects.get(pk=user_id)
        except Exception:
            return Response({'error': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save(update_fields=['password'])
        return Response({'success': True}, status=status.HTTP_200_OK)
