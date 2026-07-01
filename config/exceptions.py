"""Custom DRF exception handling."""

from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """Include machine-readable error codes in API exception responses."""
    response = exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, APIException):
        codes = exc.get_codes()
        if isinstance(codes, str):
            response.data["code"] = codes

    return response
