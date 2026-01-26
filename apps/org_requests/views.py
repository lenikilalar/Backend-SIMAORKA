"""OrgRequests views for SIMAORKA API."""

from rest_framework import views, viewsets, permissions, status
from rest_framework.request import Request
from django.utils.text import slugify
from typing import Any, cast

from common.responses import success_response, error_response, created_response
from common.exceptions import ErrorCode
from common.permissions import IsSystemAdmin

from .models import OrganizationRequest, OrgRequestStatus
from .serializers import OrgRequestSerializer, OrgRequestCreateSerializer, OrgRequestReviewSerializer


from drf_spectacular.utils import extend_schema
from common.schemas import SuccessResponseSerializer

class PublicOrgRequestView(views.APIView):
    """POST /api/v1/org-requests - Submit new org creation request (public)."""
    permission_classes: Any = [permissions.AllowAny]
    
    @extend_schema(
        summary="Submit organization request",
        request=OrgRequestCreateSerializer,
        responses={201: OrgRequestSerializer},
        tags=['OrgRequests']
    )
    def post(self, request):
        serializer = OrgRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Auto-generate slug if not provided
        data = cast(dict[str, Any], serializer.validated_data)
        if not data.get('proposed_slug'):
            data['proposed_slug'] = slugify(data['proposed_name'])
        
        # Set requester_user if authenticated
        if request.user.is_authenticated:
            data['requester_user'] = request.user
        
        org_request = OrganizationRequest.objects.create(**data)
        return created_response(OrgRequestSerializer(org_request).data)


@extend_schema(tags=['OrgRequests'])
class AdminOrgRequestViewSet(viewsets.ModelViewSet):
    """Admin endpoints for managing org requests."""
    permission_classes: Any = [permissions.IsAuthenticated, IsSystemAdmin]
    serializer_class = OrgRequestSerializer
    queryset = OrganizationRequest.objects.all().order_by('-created_at')
    
    def list(self, request: Request, *args: Any, **kwargs: Any):
        """List all requests with optional filtering."""
        queryset = self.filter_queryset(self.get_queryset())
        
        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        page = self.paginate_queryset(queryset)
        if page:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return success_response(self.get_serializer(queryset, many=True).data)
    
    def review(self, request, pk=None):
        """POST /api/v1/admin/org-requests/{id}/review - Approve/reject request."""
        try:
            org_request = self.get_queryset().get(pk=pk)
        except OrganizationRequest.DoesNotExist:
            return error_response(ErrorCode.NOT_FOUND, "Request not found", status_code=status.HTTP_404_NOT_FOUND)
        
        serializer = OrgRequestReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = cast(dict[str, Any], serializer.validated_data)
        org_request.status = data['status']
        org_request.admin_note = data.get('admin_note', '')
        org_request.handled_by = request.user
        org_request.save()
        
        # If approved, create the organization
        if org_request.status == OrgRequestStatus.APPROVED:
            from apps.organizations.models import Organization, OrgStatus
            org = Organization.objects.create(
                slug=org_request.proposed_slug,
                name=org_request.proposed_name,
                description=org_request.proposed_description,
                status=OrgStatus.ACTIVE,
                created_by=org_request.requester_user
            )
            
            # Auto-assign requester as Org Admin
            if org_request.requester_user:
                from apps.organizations.models import OrganizationMember, MemberRole, MembershipStatus
                from apps.rbac.models import Role, RoleScope
                
                # 1. Add as Member
                member, _ = OrganizationMember.objects.get_or_create(
                    organization=org,
                    user=org_request.requester_user,
                    defaults={'status': MembershipStatus.ACTIVE}
                )
                
                # 2. Grant ORG_ADMIN role
                try:
                    # Ensure ORG_ADMIN role exists (scope=ORG)
                    admin_role = Role.objects.get(code='ORG_ADMIN', scope=RoleScope.ORG)
                    MemberRole.objects.get_or_create(member=member, role=admin_role)
                except Role.DoesNotExist:
                    # Log error or silence if role setup is missing
                    print("WARNING: ORG_ADMIN role not found. Requester only added as member.")
        
        return success_response(OrgRequestSerializer(org_request).data)
