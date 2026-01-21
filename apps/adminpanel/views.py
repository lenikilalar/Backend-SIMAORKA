"""Admin panel views for SIMAORKA API."""

from rest_framework import views, viewsets, permissions, status
from rest_framework.decorators import action
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

from common.responses import success_response, error_response
from common.exceptions import ErrorCode
from common.permissions import IsSystemAdmin

from apps.organizations.models import Organization
from apps.organizations.serializers import OrganizationSerializer
from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.org_requests.models import OrganizationRequest
from apps.notifications.models import Notification


class AdminStatsView(views.APIView):
    """GET /api/v1/admin/stats - Get system-wide statistics."""
    permission_classes = [permissions.IsAuthenticated, IsSystemAdmin]
    
    @extend_schema(
        summary="Get admin dashboard statistics",
        responses={
            200: inline_serializer(
                name='AdminStatsResponse',
                fields={
                    'users': serializers.DictField(),
                    'organizations': serializers.DictField(),
                    'org_requests': serializers.DictField(),
                    'activity': serializers.DictField(),
                }
            )
        }
    )
    def get(self, request):
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        last_7_days = now - timedelta(days=7)
        
        stats = {
            'users': {
                'total': User.objects.count(),
                'active': User.objects.filter(is_active=True).count(),
                'new_last_30_days': User.objects.filter(date_joined__gte=last_30_days).count(),
            },
            'organizations': {
                'total': Organization.objects.count(),
                'active': Organization.objects.filter(status='active').count(),
            },
            'org_requests': {
                'pending': OrganizationRequest.objects.filter(status='submitted').count(),
                'in_review': OrganizationRequest.objects.filter(status='in_review').count(),
                'total': OrganizationRequest.objects.count(),
            },
            'activity': {
                'audit_logs_last_7_days': AuditLog.objects.filter(created_at__gte=last_7_days).count(),
                'notifications_last_7_days': Notification.objects.filter(created_at__gte=last_7_days).count(),
            }
        }
        
        return success_response(stats)



class AdminOrgsViewSet(viewsets.ModelViewSet):
    """Admin endpoints for managing organizations."""
    permission_classes = [permissions.IsAuthenticated, IsSystemAdmin]
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    
    @extend_schema(
        summary="List all organizations (admin)",
        parameters=[
            {'name': 'status', 'in': 'query', 'schema': {'type': 'string'}}
        ]
    )
    def list(self, request):
        queryset = self.get_queryset()
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        page = self.paginate_queryset(queryset)
        if page:
            return self.get_paginated_response(OrganizationSerializer(page, many=True).data)
        return success_response(OrganizationSerializer(queryset, many=True).data)
    
    @extend_schema(
        summary="Update organization (admin)",
        request=OrganizationSerializer,
        responses={200: OrganizationSerializer}
    )
    def partial_update(self, request, pk=None):
        """PATCH to update org status, etc."""
        try:
            org = self.get_queryset().get(pk=pk)
        except Organization.DoesNotExist:
            return error_response(ErrorCode.NOT_FOUND, "Organization not found", status_code=status.HTTP_404_NOT_FOUND)
        
        serializer = OrganizationSerializer(org, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(serializer.data)


class SetAdminView(views.APIView):
    """POST /api/v1/admin/set-admin - Grant admin role to a user."""
    permission_classes = [permissions.IsAuthenticated, IsSystemAdmin]
    
    @extend_schema(
        summary="Grant admin role to user",
        request=inline_serializer(
            name='SetAdminRequest',
            fields={
                'user_id': serializers.UUIDField(),
                'role_code': serializers.CharField(default='CAMPUS_ADMIN'),
            }
        ),
        responses={
            200: inline_serializer(
                name='SetAdminResponse',
                fields={
                    'message': serializers.CharField(),
                    'user_id': serializers.CharField(),
                    'role_code': serializers.CharField(),
                }
            )
        }
    )
    def post(self, request):
        user_id = request.data.get('user_id')
        role_code = request.data.get('role_code', 'CAMPUS_ADMIN')
        
        if not user_id:
            return error_response(ErrorCode.VALIDATION_ERROR, "user_id required", status_code=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return error_response(ErrorCode.NOT_FOUND, "User not found", status_code=status.HTTP_404_NOT_FOUND)
        
        # Grant system-level admin role
        from apps.rbac.models import Role
        from apps.organizations.models import OrganizationMember, MemberRole
        
        try:
            role = Role.objects.get(code=role_code, scope='SYSTEM')
        except Role.DoesNotExist:
            return error_response(ErrorCode.NOT_FOUND, f"Role {role_code} not found", status_code=status.HTTP_404_NOT_FOUND)
        
        # For system admin, we use is_staff flag
        user.is_staff = True
        user.save()
        
        return success_response({
            'message': f'User {user.email} granted {role_code} role',
            'user_id': str(user.id),
            'role_code': role_code
        })

