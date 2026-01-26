"""
File upload views for SIMAORKA API.
Handles profile photos, org logos, document uploads, etc.
"""

from rest_framework import views, parsers, permissions, status, renderers
from rest_framework.response import Response
from typing import cast, Any
from django.conf import settings

from common.responses import success_response, error_response
from common.exceptions import ErrorCode
from common.storage import upload_file, get_signed_url, delete_file
from drf_spectacular.utils import extend_schema


class BaseUploadView(views.APIView):
    """Base class for file uploads."""
    permission_classes: Any = [permissions.IsAuthenticated]
    parser_classes: Any = [parsers.MultiPartParser, parsers.FormParser]
    
    folder = 'uploads'
    allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx']
    max_file_size = 10 * 1024 * 1024  # 10MB
    
    def validate_file(self, file):
        """Validate file extension and size."""
        if not file:
            return False, "No file provided"
        
        # Check extension
        ext = file.name.split('.')[-1].lower() if '.' in file.name else ''
        if ext not in self.allowed_extensions:
            return False, f"File type '{ext}' not allowed. Allowed: {', '.join(self.allowed_extensions)}"
        
        # Check size
        if file.size > self.max_file_size:
            return False, f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB"
        
        return True, None
    
    def post(self, request):
        file = request.FILES.get('file')
        
        valid, error_msg = self.validate_file(file)
        if not valid:
            return error_response(
                ErrorCode.VALIDATION_ERROR,
                error_msg,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            upload_result = upload_file(file, self.folder)
            path = upload_result['path']
            
            # If we need a signed URL (private access), generate it
            # Otherwise use the public URL returned by upload_file
            if settings.STORAGE_BACKEND == 'local':
                 url = upload_result['url']
            else:
                 url = get_signed_url(path) if settings.DEBUG else get_signed_url(path, expiration=86400)
            
            return success_response({
                'path': path,
                'url': url,
                'filename': file.name,
                'size': file.size
            }, status_code=status.HTTP_201_CREATED)
        except Exception as e:
            return error_response(
                ErrorCode.SERVER_ERROR,
                f"Upload failed: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(tags=['Uploads'])
class ProfilePhotoUploadView(BaseUploadView):
    """POST /api/v1/uploads/profile-photo - Upload user profile photo."""
    folder = 'profile-photos'
    allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    max_file_size = 5 * 1024 * 1024  # 5MB
    
    def post(self, request):
        response = super().post(request)
        
        # If upload successful, update user's profile
        if response.status_code == status.HTTP_201_CREATED:
            try:
                profile = request.user.profile
                # Delete old photo if exists
                if profile.profile_photo_url:
                    old_path = profile.profile_photo_url.split('/')[-1] if '/' in str(profile.profile_photo_url) else None
                    if old_path:
                        delete_file(f"profile-photos/{old_path}")
                
                # Update profile with new path
                from typing import cast, Any
                data = cast(dict[str, Any], response.data)
                profile.profile_photo_url = data['data']['url']
                profile.save(update_fields=['profile_photo_url'])
            except Exception:
                pass  # Profile update not critical
        
        return response


@extend_schema(tags=['Uploads'])
class OrgLogoUploadView(BaseUploadView):
    """POST /api/v1/uploads/org-logo - Upload organization logo."""
    folder = 'org-logos'
    allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']
    max_file_size = 5 * 1024 * 1024  # 5MB


@extend_schema(tags=['Uploads'])
class NewsCoverUploadView(BaseUploadView):
    """POST /api/v1/uploads/news-cover - Upload news article cover image."""
    folder = 'news-covers'
    allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    max_file_size = 10 * 1024 * 1024  # 10MB


@extend_schema(tags=['Uploads'])
class FinanceAttachmentUploadView(BaseUploadView):
    """POST /api/v1/uploads/finance-attachment - Upload finance transaction attachment."""
    folder = 'finance-attachments'
    allowed_extensions = ['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx', 'xls', 'xlsx']
    max_file_size = 10 * 1024 * 1024  # 10MB


@extend_schema(tags=['Uploads'])
class DocumentUploadView(BaseUploadView):
    """POST /api/v1/uploads/document - Upload organization document."""
    folder = 'documents'
    allowed_extensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'zip']
    max_file_size = 50 * 1024 * 1024  # 50MB


@extend_schema(tags=['Uploads'])
class GetSignedUrlView(views.APIView):
    """GET /api/v1/uploads/signed-url - Get a signed URL for private file access."""
    permission_classes: Any = [permissions.IsAuthenticated]
    
    def get(self, request):
        path = request.query_params.get('path')
        expiration = int(request.query_params.get('expiration', 3600))
        
        if not path:
            return error_response(
                ErrorCode.VALIDATION_ERROR,
                "Path parameter is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Limit expiration to 24 hours
        expiration = min(expiration, 86400)
        
        try:
            url = get_signed_url(path, expiration)
            return success_response({'url': url, 'expires_in': expiration})
        except Exception as e:
            return error_response(
                ErrorCode.NOT_FOUND,
                f"File not found: {str(e)}",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                ErrorCode.NOT_FOUND,
                f"File not found: {str(e)}",
                status_code=status.HTTP_404_NOT_FOUND
            )


@extend_schema(exclude=True)
class LogViewerView(views.APIView):
    """
    Internal view to display logs.
    Authenticated Staff only (or public in DEBUG mode).
    """
    permission_classes: Any = [permissions.AllowAny]
    renderer_classes: Any = [renderers.TemplateHTMLRenderer]

    def get(self, request):
        from django.conf import settings
        from django.shortcuts import render
        import os

        # Security check: Allow if DEBUG=True OR User is Staff
        if not settings.DEBUG and not request.user.is_staff:
             return error_response(ErrorCode.PERMISSION_DENIED, "Admins only.", status_code=status.HTTP_403_FORBIDDEN)

        # Manually render template response
        log_file = settings.BASE_DIR / 'logs' / 'requests.log'
        logs = []
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                # Read lines, reverse to show newest first
                lines = f.readlines()
                for line in reversed(lines[-200:]): # Show last 200 lines
                    if not line.strip(): continue
                    
                    try:
                        # Format: 2026-01-25 13:00:00,000 INFO REQ/RES ...
                        parts = line.split(' ', 3)
                        timestamp = parts[0] + ' ' + parts[1]
                        level = parts[2]
                        message = parts[3]
                        
                        entry_type = 'INFO'
                        if 'REQ' in message:
                            entry_type = 'REQ'
                            color = 'is-info'
                        elif 'RES' in message:
                            entry_type = 'RES'
                            # Check status code
                            if 'RES 2' in message: color = 'is-success'
                            elif 'RES 4' in message: color = 'is-warning'
                            elif 'RES 5' in message: color = 'is-danger'
                            else: color = 'is-primary'
                        else:
                            entry_type = 'SYS'
                            color = 'is-dark'

                        logs.append({
                            'timestamp': timestamp,
                            'level': level,
                            'type': entry_type,
                            'message': message,
                            'color': color
                        })
                    except:
                        logs.append({'timestamp': '-', 'message': line, 'color': 'is-light'})

        return render(request, 'common/log_viewer.html', {'logs': logs})
