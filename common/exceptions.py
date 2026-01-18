"""
Custom exceptions and global exception handler for SIMAORKA API.
"""

from rest_framework.views import exception_handler
from rest_framework import status


# Error codes
class ErrorCode:
    # Auth
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    UNAUTHORIZED = "UNAUTHORIZED"
    
    # Profile
    PROFILE_INCOMPLETE = "PROFILE_INCOMPLETE"
    
    # Organization
    ORG_NOT_FOUND = "ORG_NOT_FOUND"
    NOT_ORG_MEMBER = "NOT_ORG_MEMBER"
    ALREADY_MEMBER = "ALREADY_MEMBER"
    MEMBERSHIP_CLOSED = "MEMBERSHIP_CLOSED"
    
    # Permission
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INSUFFICIENT_ROLE = "INSUFFICIENT_ROLE"
    
    # Web3
    WEB3_TX_INVALID = "WEB3_TX_INVALID"
    WALLET_NOT_VERIFIED = "WALLET_NOT_VERIFIED"
    NFT_EXPIRED = "NFT_EXPIRED"
    
    # Voting
    VOTE_ALREADY_CAST = "VOTE_ALREADY_CAST"
    VOTE_CLOSED = "VOTE_CLOSED"
    
    # General
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    SERVER_ERROR = "SERVER_ERROR"


class APIException(Exception):
    """Base API exception with error code support."""
    
    def __init__(self, code, message, details=None, status_code=status.HTTP_400_BAD_REQUEST):
        self.code = code
        self.message = message
        self.details = details
        self.status_code = status_code
        super().__init__(message)


class ProfileIncompleteException(APIException):
    def __init__(self, message="Profile is incomplete. Please complete your profile first."):
        super().__init__(ErrorCode.PROFILE_INCOMPLETE, message, status_code=status.HTTP_403_FORBIDDEN)


class PermissionDeniedException(APIException):
    def __init__(self, message="You do not have permission to perform this action."):
        super().__init__(ErrorCode.PERMISSION_DENIED, message, status_code=status.HTTP_403_FORBIDDEN)


class MembershipClosedException(APIException):
    def __init__(self, message="Membership registration is currently closed."):
        super().__init__(ErrorCode.MEMBERSHIP_CLOSED, message, status_code=status.HTTP_400_BAD_REQUEST)


class Web3TxInvalidException(APIException):
    def __init__(self, message="Web3 transaction verification failed.", details=None):
        super().__init__(ErrorCode.WEB3_TX_INVALID, message, details, status_code=status.HTTP_400_BAD_REQUEST)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that formats all errors in envelope format.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Format DRF exceptions
        error_data = {
            "error": {
                "code": ErrorCode.VALIDATION_ERROR,
                "message": "Validation error",
                "details": response.data
            }
        }
        response.data = error_data
        return response
    
    # Handle our custom APIException
    if isinstance(exc, APIException):
        from rest_framework.response import Response
        error_data = {
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        }
        if exc.details:
            error_data["error"]["details"] = exc.details
        return Response(error_data, status=exc.status_code)
    
    return response
