from rest_framework import viewsets, permissions, status, filters, serializers, views
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.text import slugify
from django.db.models import Count
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, inline_serializer
from common.schemas import PaginatedResponseSerializer
from typing import Any, cast

from .models import Organization, OrganizationMember, MembershipStatus
from apps.org_requests.models import OrganizationRequest
from common.responses import success_response, error_response
from common.exceptions import ErrorCode
from .serializers import (
    OrganizationSerializer, OrganizationMemberSerializer, 
    OrganizationRequestSerializer, PublicOrganizationSerializer
)

@extend_schema(tags=['Organizations'])
class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    filter_backends: Any = [filters.SearchFilter]
    search_fields = ['name', 'slug']
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'news', 'events', 'public_list']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        name = serializer.validated_data.get('name')
        slug = slugify(name)
        if Organization.objects.filter(slug=slug).exists():
            import uuid
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"
        serializer.save(created_by=self.request.user, slug=slug)

    @extend_schema(
        summary="List public organizations",
        parameters=[
            OpenApiParameter('page', OpenApiTypes.INT, description='Page number'),
            OpenApiParameter('page_size', OpenApiTypes.INT, description='Items per page'),
            OpenApiParameter('search', OpenApiTypes.STR, description='Search by name'),
            OpenApiParameter('category', OpenApiTypes.STR, description='Filter by category'),
        ],
        responses={200: PaginatedResponseSerializer}
    )
    @action(detail=False, methods=['get'])
    def public_list(self, request):
        queryset = cast(Any, self.queryset).filter(status='active', is_private=False).annotate(member_count=Count('members'))
        
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
            
        # Category filter placeholder (model has no category field yet)
        # category = request.query_params.get('category')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PublicOrganizationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PublicOrganizationSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get organization members",
        responses={200: OrganizationMemberSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def members(self, request, slug=None):
        org = self.get_object()
        members = org.members.all()
        serializer = OrganizationMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def applications(self, request, slug=None):
        org = self.get_object()
        
        # Check permission: Requester must be ORG_ADMIN
        from apps.organizations.models import MemberRole
        is_admin = MemberRole.objects.filter(
            member__organization=org,
            member__user=request.user,
            role__code='ORG_ADMIN'
        ).exists()
        
        if not is_admin and not request.user.is_superuser:
            return error_response(ErrorCode.PERMISSION_DENIED, "Only Organization Admins can view applications.", status_code=status.HTTP_403_FORBIDDEN)

        applications = OrganizationMember.objects.filter(
            organization=org,
            status=MembershipStatus.PENDING
        ).select_related('user', 'user__profile').order_by('-created_at')
        
        page = self.paginate_queryset(applications)
        if page is not None:
            serializer = OrganizationMemberSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = OrganizationMemberSerializer(applications, many=True)
        return success_response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def apply(self, request, slug=None):
        org = self.get_object()
        # Check if already member
        if OrganizationMember.objects.filter(organization=org, user=request.user).exists():
            return error_response(ErrorCode.ALREADY_MEMBER, 'Already a member (or pending)', status_code=status.HTTP_400_BAD_REQUEST)
        
        OrganizationMember.objects.create(
            organization=org,
            user=request.user,
            status=MembershipStatus.PENDING
        )
        return success_response({'message': 'Application submitted'}, status_code=status.HTTP_201_CREATED)

@extend_schema(tags=['Organization Members'])
class OrganizationMemberViewSet(viewsets.ModelViewSet):
    queryset = OrganizationMember.objects.all()
    serializer_class = OrganizationMemberSerializer
    permission_classes: Any = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Set organization role for member",
        request=inline_serializer(
            name='SetRoleRequest',
            fields={'role_code': serializers.CharField()}
        ),
        responses={200: OrganizationMemberSerializer}
    )
    @action(detail=True, methods=['post'])
    def set_role(self, request, pk=None):
        member = self.get_object()
        
        # Check permission: Requester must be ORG_ADMIN of this organization
        # OR be a System Admin
        from apps.organizations.models import MemberRole
        from apps.rbac.models import Role, RoleScope
        
        # Simple check: Requester must be admin of the org
        # Use helper or check manually
        requester_is_admin = MemberRole.objects.filter(
            member__organization=member.organization,
            member__user=request.user,
            role__code='ORG_ADMIN'
        ).exists()
        
        if not requester_is_admin and not request.user.is_superuser:
             return error_response(ErrorCode.PERMISSION_DENIED, "Only Organization Admins can assign roles.", status_code=status.HTTP_403_FORBIDDEN)
             
        role_code = request.data.get('role_code')
        if not role_code:
            return error_response(ErrorCode.VALIDATION_ERROR, "role_code required")
            
        try:
            role = Role.objects.get(code=role_code, scope=RoleScope.ORG)
        except Role.DoesNotExist:
            return error_response(ErrorCode.NOT_FOUND, f"Role {role_code} not found or not organization-scoped")
            
        # Assign role
        MemberRole.objects.get_or_create(member=member, role=role)
        
        return success_response(self.get_serializer(member).data)

@extend_schema(tags=['OrgRequests'])
class OrganizationRequestViewSet(viewsets.ModelViewSet):
    queryset = OrganizationRequest.objects.all()
    serializer_class = OrganizationRequestSerializer
    permission_classes: Any = [permissions.AllowAny] # Allow public to request

    def perform_create(self, serializer):
        # If user is auth, could link them. For now just save.
        serializer.save()


class UserOrganizationsView(views.APIView):
    """
    GET /api/v1/me/organizations/
    List organizations where current user is a member.
    """
    permission_classes: Any = [permissions.IsAuthenticated]

    @extend_schema(
        summary="List my organizations",
        responses={200: OrganizationSerializer(many=True)},
        tags=['Organizations']
    )
    def get(self, request):
        # Filter orgs where user is a member (active or pending?)
        # TSD says "list of joined orgs", usually implies active. 
        # But showing pending might be useful. Let's show all or just active?
        # Let's show all for now, or filter by status if needed.
        # Assuming Active for "My Organizations" usually.
        
        orgs = Organization.objects.filter(
            members__user=request.user,
            members__status=MembershipStatus.ACTIVE
        ).distinct()
        
        serializer = OrganizationSerializer(orgs, many=True)
        return success_response(serializer.data)
