from django.db import OperationalError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def api_exception_handler(exc, context):
    """
    Convert transient DB connectivity failures into a controlled API 503.
    """
    response = drf_exception_handler(exc, context)
    if response is not None:
        return response

    if isinstance(exc, OperationalError):
        return Response(
            {"detail": "Database temporarily unavailable. Please retry."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return response
