"""Audit views for SIMAORKA API (admin only)."""

from rest_framework import viewsets, permissions

from common.responses import success_response
from common.permissions import IsSystemAdmin

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin endpoint for viewing audit logs."""
    permission_classes = [permissions.IsAuthenticated, IsSystemAdmin]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()
    
    def list(self, request):
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
