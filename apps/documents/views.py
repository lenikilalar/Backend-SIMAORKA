"""
Documents views for SIMAORKA API.
"""

import hashlib
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from common.responses import success_response, error_response
from common.exceptions import ErrorCode
from common.storage import upload_file, get_signed_url
from common.permissions import IsOrgMemberActive

from .models import Document, DocumentVersion, DocumentAccessRule, DocumentStatus
from .serializers import (
    DocumentSerializer, DocumentCreateSerializer,
    DocumentVersionSerializer, DocumentAccessRuleSerializer
)


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for organization documents.
    
    GET /api/v1/orgs/{org_id}/documents - List org documents
    POST /api/v1/orgs/{org_id}/documents - Create document
    GET /api/v1/orgs/{org_id}/documents/{id} - Get document detail
    PUT/PATCH /api/v1/orgs/{org_id}/documents/{id} - Update document
    DELETE /api/v1/orgs/{org_id}/documents/{id} - Delete document
    POST /api/v1/orgs/{org_id}/documents/{id}/upload - Upload new version
    GET /api/v1/orgs/{org_id}/documents/{id}/download - Download latest version
    GET /api/v1/orgs/{org_id}/documents/{id}/versions - List versions
    """
    permission_classes = [permissions.IsAuthenticated, IsOrgMemberActive]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DocumentCreateSerializer
        return DocumentSerializer
    
    def get_queryset(self):
        org_id = self.kwargs.get('org_id')
        queryset = Document.objects.filter(organization_id=org_id)
        
        # Filter by status if provided
        doc_status = self.request.query_params.get('status')
        if doc_status:
            queryset = queryset.filter(status=doc_status)
        
        return queryset.prefetch_related('versions')
    
    def list(self, request, org_id=None):
        queryset = self.get_queryset()
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)
    
    def create(self, request, org_id=None):
        data = request.data.copy()
        data['organization'] = org_id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save(created_by=request.user)
        
        return success_response(
            DocumentSerializer(document).data,
            status_code=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, pk=None, org_id=None):
        try:
            document = self.get_queryset().get(pk=pk)
            serializer = self.get_serializer(document)
            return success_response(serializer.data)
        except Document.DoesNotExist:
            return error_response(
                ErrorCode.NOT_FOUND,
                "Document not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request, pk=None, org_id=None):
        """Upload a new version of the document."""
        try:
            document = self.get_queryset().get(pk=pk)
        except Document.DoesNotExist:
            return error_response(
                ErrorCode.NOT_FOUND,
                "Document not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        file = request.FILES.get('file')
        if not file:
            return error_response(
                ErrorCode.VALIDATION_ERROR,
                "No file provided",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate file hash
        hasher = hashlib.sha256()
        for chunk in file.chunks():
            hasher.update(chunk)
        file_hash = hasher.hexdigest()
        file.seek(0)  # Reset file pointer
        
        # Upload file
        file_path = upload_file(file, f'documents/{org_id}')
        
        # Get next version number
        last_version = document.versions.first()
        version_number = (last_version.version_number + 1) if last_version else 1
        
        # Create version record
        version = DocumentVersion.objects.create(
            document=document,
            version_number=version_number,
            file_path=file_path,
            file_hash=file_hash,
            file_size=file.size,
            uploaded_by=request.user
        )
        
        return success_response(
            DocumentVersionSerializer(version).data,
            status_code=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None, org_id=None):
        """Get signed URL for downloading the latest version."""
        try:
            document = self.get_queryset().get(pk=pk)
        except Document.DoesNotExist:
            return error_response(
                ErrorCode.NOT_FOUND,
                "Document not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        latest = document.versions.first()
        if not latest:
            return error_response(
                ErrorCode.NOT_FOUND,
                "No versions available",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        url = get_signed_url(latest.file_path, expiration=3600)
        
        return success_response({
            'url': url,
            'version': latest.version_number,
            'file_hash': latest.file_hash,
            'expires_in': 3600
        })
    
    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None, org_id=None):
        """List all versions of a document."""
        try:
            document = self.get_queryset().get(pk=pk)
        except Document.DoesNotExist:
            return error_response(
                ErrorCode.NOT_FOUND,
                "Document not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        versions = document.versions.all()
        return success_response(DocumentVersionSerializer(versions, many=True).data)
