"""OrgRequests views for SIMAORKA API."""

from rest_framework import views, viewsets, permissions, status
from django.utils.text import slugify

from common.responses import success_response, error_response, created_response
from common.exceptions import ErrorCode
from common.permissions import IsSystemAdmin

from .models import OrganizationRequest, OrgRequestStatus
from .serializers import OrgRequestSerializer, OrgRequestCreateSerializer, OrgRequestReviewSerializer


from drf_spectacular.utils import extend_schema
from common.schemas import SuccessResponseSerializer

class PublicOrgRequestView(views.APIView):
    """POST /api/v1/org-requests - Submit new org creation request (public)."""
    permission_classes = [permissions.AllowAny]
    
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
        data = serializer.validated_data
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
    permission_classes = [permissions.IsAuthenticated, IsSystemAdmin]
    serializer_class = OrgRequestSerializer
    queryset = OrganizationRequest.objects.all().order_by('-created_at')
    
    def list(self, request):
        queryset = self.get_queryset()
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
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
        
        org_request.status = serializer.validated_data['status']
        org_request.admin_note = serializer.validated_data.get('admin_note', '')
        org_request.handled_by = request.user
        org_request.save()
        
        # If approved, create the organization
        if org_request.status == OrgRequestStatus.APPROVED:
            from apps.organizations.models import Organization, OrgStatus
            Organization.objects.create(
                slug=org_request.proposed_slug,
                name=org_request.proposed_name,
                description=org_request.proposed_description,
                status=OrgStatus.ACTIVE,
                created_by=org_request.requester_user
            )
        
        return success_response(OrgRequestSerializer(org_request).data)
