"""Admin panel views for SIMAORKA API."""

from rest_framework import viewsets, permissions, status, views, serializers, filters
from typing import cast, Any
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.request import Request
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiParameter, OpenApiTypes

from common.responses import success_response, error_response
from common.exceptions import ErrorCode
from common.permissions import IsSystemAdmin

from apps.organizations.models import Organization
from apps.organizations.serializers import OrganizationSerializer
from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.org_requests.models import OrganizationRequest
from apps.notifications.models import Notification


from .serializers import AdminStatsSerializer

class AdminDashboardView(APIView):
    """
    POST /api/v1/admin/set-admin
    """
    permission_classes: Any = [permissions.IsAuthenticated, IsSystemAdmin]
    
    @extend_schema(
        summary="Get admin dashboard statistics",
        responses={200: AdminStatsSerializer},
        tags=['Admin']
    )
    def get(self, request):
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        
        # Imports for counts
        from apps.events.models import Event
        from apps.content.models import Announcement
        
        stats = {
            'total_users': User.objects.count(),
            'total_organizations': Organization.objects.count(),
            'active_organizations': Organization.objects.filter(status='active').count(),
            'pending_requests': OrganizationRequest.objects.filter(status='submitted').count(),
            'total_events': Event.objects.count(),
            'total_announcements': Announcement.objects.count(),
            'users_this_month': User.objects.filter(date_joined__gte=last_30_days).count(),
            'orgs_this_month': Organization.objects.filter(created_at__gte=last_30_days).count()
        }
        
        return success_response(stats)



@extend_schema(tags=['Admin'])
class AdminOrgsViewSet(viewsets.ModelViewSet):
    """Admin endpoints for managing organizations."""
    permission_classes: Any = [permissions.IsAuthenticated, IsSystemAdmin]
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    
    @extend_schema(
        summary="List all organizations (admin)",
        parameters=[
            OpenApiParameter(name='status', location=OpenApiParameter.QUERY, type=str, description='Filter by status')
        ]
    )
    def list(self, request, *args: Any, **kwargs: Any):
        # Add summary stats to each org
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page:
            return self.get_paginated_response(OrganizationSerializer(page, many=True).data)
        return success_response(OrganizationSerializer(queryset, many=True).data)
    
    @extend_schema(
        summary="Update organization (admin)",
        request=OrganizationSerializer,
        responses={200: OrganizationSerializer}
    )
    def partial_update(self, request, *args: Any, **kwargs: Any):
        pk = kwargs.get('pk')
        try:
            org = self.get_queryset().get(pk=pk)
        except Organization.DoesNotExist:
            return error_response(ErrorCode.NOT_FOUND, "Organization not found", status_code=status.HTTP_404_NOT_FOUND)
        
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(serializer.data)


class SetAdminView(views.APIView):
    """POST /api/v1/admin/set-admin - Grant admin role to a user."""
    permission_classes: Any = [permissions.IsAuthenticated, IsSystemAdmin]
    
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
        },
        tags=['Admin']
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


@extend_schema(tags=['Admin'])
class AdminUsersViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin endpoint to list and search all users.
    """
    permission_classes: Any = [permissions.IsAuthenticated, IsSystemAdmin]
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = serializers.Serializer  # Placeholder, will use UserSerializer
    
    # We need to import UserSerializer properly or use a local one
    # To avoid circular imports, we might need to be careful, but apps.accounts is distinct.
    
    def get_serializer_class(self) -> Any:
        from apps.accounts.serializers import UserSerializer
        return UserSerializer

    filter_backends: Any = [filters.SearchFilter]
    search_fields = ['email', 'profile__full_name', 'profile__nim']

    @extend_schema(
        summary="List all users (admin)",
        parameters=[
            OpenApiParameter('search', OpenApiTypes.STR, description='Search by email, name, or NIM'),
            OpenApiParameter('page', OpenApiTypes.INT, description='Page number'),
        ]
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

