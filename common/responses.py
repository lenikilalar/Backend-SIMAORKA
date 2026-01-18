"""
API Response envelope helpers following TSD V2 specification.
All responses follow:
- Success: {"data": ..., "meta": {...}}
- Error: {"error": {"code": "CODE", "message": "msg", "details": {...}}}
"""

from rest_framework.response import Response
from rest_framework import status


def success_response(data=None, meta=None, status_code=status.HTTP_200_OK):
    """
    Return a successful API response in envelope format.
    """
    response_data = {"data": data}
    if meta:
        response_data["meta"] = meta
    return Response(response_data, status=status_code)


def error_response(code, message, details=None, status_code=status.HTTP_400_BAD_REQUEST):
    """
    Return an error API response in envelope format.
    """
    error_data = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details:
        error_data["error"]["details"] = details
    return Response(error_data, status=status_code)


def created_response(data=None, meta=None):
    """Shortcut for 201 Created responses."""
    return success_response(data, meta, status.HTTP_201_CREATED)


def paginated_response(data, page_info):
    """
    Return paginated response with meta information.
    page_info should contain: count, next, previous, page_size
    """
    return success_response(data, meta=page_info)
