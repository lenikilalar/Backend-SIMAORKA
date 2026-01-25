"""Audit views for SIMAORKA API (admin only)."""

from rest_framework import viewsets, permissions
from rest_framework.request import Request
from typing import cast, Any

from common.responses import success_response
from common.permissions import IsSystemAdmin

from .models import AuditLog
from .serializers import AuditLogSerializer
from drf_spectacular.utils import extend_schema


@extend_schema(tags=['Audit'])
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin endpoint for viewing audit logs."""
    permission_classes: Any = [permissions.IsAuthenticated, IsSystemAdmin]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()
    
    def list(self, request: Request, *args: Any, **kwargs: Any):
        queryset = self.get_queryset()
        
        # Filters
        user_id = request.query_params.get('user_id')
        org_id = request.query_params.get('org_id')
        action = request.query_params.get('action')
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        if action:
            queryset = queryset.filter(action__icontains=action)
        
        page = self.paginate_queryset(queryset)
        if page:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return success_response(self.get_serializer(queryset, many=True).data)
