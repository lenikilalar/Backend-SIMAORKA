"""
Middleware for SIMAORKA API.
"""

import json
import logging
import time
from typing import cast, Any
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


class RequestLoggingMiddleware:
    """
    Middleware to log detailed request and response information.
    Masks sensitive data in headers and body.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.sensitive_headers = {'Authorization', 'Cookie', 'X-CSRFToken'}
        self.sensitive_keys = {
            'password', 'confirm_password', 'token', 'refresh', 'access', 
            'secret', 'client_secret', 'credit_card'
        }

    def __call__(self, request):
        start_time = time.time()
        
        # Skip logging for log viewer to avoid infinite loops/noise
        if 'api/v1/logs' in request.path:
            return self.get_response(request)

        # Log Request
        self._log_request(request)
        
        response = self.get_response(request)
        
        # Log Response
        duration = time.time() - start_time
        self._log_response(request, response, duration)
        
        return response

    def _log_request(self, request):
        """Log incoming request details."""
        try:
            # Mask headers
            headers = {}
            for k, v in request.META.items():
                if k.startswith('HTTP_'):
                    header_name = k[5:].replace('_', '-').title()
                    if header_name in self.sensitive_headers:
                        headers[header_name] = '***MASKED***'
                    else:
                        headers[header_name] = v
            
            # Body
            body = {}
            if request.content_type == 'application/json':
                try:
                    if request.body:
                        body_json = json.loads(request.body)
                        body = self._mask_sensitive_data(body_json)
                except Exception:
                    body = '***INVALID JSON***'
            elif request.POST:
                # Log Form Data
                try:
                    body = self._mask_sensitive_data(request.POST.dict())
                except Exception:
                    pass
            
            # Append File Metadata
            if request.FILES:
                files_info = {}
                for key, file in request.FILES.items():
                    files_info[key] = {
                        'name': file.name,
                        'size': f"{file.size / 1024:.2f} KB",
                        'type': file.content_type
                    }
                if isinstance(body, dict):
                    body['FILES'] = files_info
                else:
                    body = {'DATA': body, 'FILES': files_info}

            elif request.body and request.method not in ['GET', 'HEAD']:
                 # Only mask as binary if there is actual content we didn't parse
                 body = '***BINARY/FORM-DATA***'
            
            user = request.user if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous'
            
            logger.info(
                f"REQ {request.method} {request.path} | "
                f"User: {user} | "
                f"Body: {body}"
            )
        except Exception as e:
            logger.error(f"Error logging request: {e}")

    def _log_response(self, request, response, duration):
        """Log outgoing response details."""
        try:
            content = '***STREAM/BINARY***'
            if hasattr(response, 'data'):
                # DRF Response
                content = self._mask_sensitive_data(response.data)
            elif response.get('Content-Type', '').startswith('application/json'):
                # Regular Django JsonResponse
                try:
                    content_json = json.loads(response.content.decode('utf-8'))
                    content = self._mask_sensitive_data(content_json)
                except:
                    pass
            
            # Fallback: Try decoding text content for errors or text responses
            if content == '***STREAM/BINARY***' and hasattr(response, 'content'):
                try:
                    # Simplify content type check
                    ctype = response.get('Content-Type', '')
                    is_text = 'text' in ctype or 'html' in ctype or 'xml' in ctype
                    is_error = response.status_code >= 400
                    
                    if is_text or is_error:
                        decoded = response.content.decode('utf-8', errors='replace')
                        # Sanitize if it looks like HTML (basic)
                        if '<html' in decoded:
                            decoded = "HTML Error Page (truncated): " + decoded[:200]
                        content = decoded
                except:
                    pass
            
            # Truncate long content
            content_str = str(content)
            if len(content_str) > 1000:
                content_str = content_str[:1000] + '... (truncated)'

            logger.info(
                f"RES {response.status_code} {request.method} {request.path} | "
                f"Content: {content_str}"
            )
        except Exception as e:
            logger.error(f"Error logging response: {e}")

    def _mask_sensitive_data(self, data):
        """Recursively mask sensitive keys in a dictionary or list."""
        if isinstance(data, dict):
            return {
                k: '***MASKED***' if k in self.sensitive_keys else self._mask_sensitive_data(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        return data

    def _get_client_ip(self, request):
        """Get client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
