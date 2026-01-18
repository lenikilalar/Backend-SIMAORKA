"""
Middleware for SIMAORKA API.
"""

import json
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class AuditLogMiddleware:
    """
    Middleware to log sensitive actions to audit_logs table.
    """
    
    AUDITED_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    AUDITED_PATHS = [
        '/api/v1/admin/',
        '/api/v1/orgs/',
        '/api/v1/auth/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process request
        response = self.get_response(request)
        
        # Log if auditable
        if self._should_audit(request, response):
            self._create_audit_log(request, response)
        
        return response

    def _should_audit(self, request, response):
        """Determine if this request should be audited."""
        if request.method not in self.AUDITED_METHODS:
            return False
        
        for path in self.AUDITED_PATHS:
            if request.path.startswith(path):
                return True
        
        return False

    def _create_audit_log(self, request, response):
        """Create an audit log entry."""
        try:
            from apps.audit.models import AuditLog
            
            user = request.user if request.user.is_authenticated else None
            
            # Extract org_id from path if present
            org_id = None
            path_parts = request.path.split('/')
            if 'orgs' in path_parts:
                org_index = path_parts.index('orgs')
                if org_index + 1 < len(path_parts):
                    org_id = path_parts[org_index + 1]
            
            AuditLog.objects.create(
                user=user,
                action=f"{request.method} {request.path}",
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                status_code=response.status_code,
                organization_id=org_id if org_id and org_id != '' else None,
            )
        except Exception as e:
            logger.warning(f"Failed to create audit log: {e}")

    def _get_client_ip(self, request):
        """Get client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
