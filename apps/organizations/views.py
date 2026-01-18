from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.text import slugify
from .models import Organization, OrganizationMember, MembershipStatus
from apps.org_requests.models import OrganizationRequest
from .serializers import OrganizationSerializer, OrganizationMemberSerializer, OrganizationRequestSerializer

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    filter_backends = [filters.SearchFilter]
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

    @action(detail=False, methods=['get'])
    def public_list(self, request):
        queryset = self.queryset.filter(status='active', is_private=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def members(self, request, slug=None):
        org = self.get_object()
        members = org.members.all()
        serializer = OrganizationMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def apply(self, request, slug=None):
        org = self.get_object()
        # Check if already member
        if OrganizationMember.objects.filter(organization=org, user=request.user).exists():
            return Response({'error': 'Already a member (or pending)'}, status=status.HTTP_400_BAD_REQUEST)
        
        OrganizationMember.objects.create(
            organization=org,
            user=request.user,
            status=MembershipStatus.PENDING
        )
        return Response({'message': 'Application submitted'}, status=status.HTTP_201_CREATED)

class OrganizationMemberViewSet(viewsets.ModelViewSet):
    queryset = OrganizationMember.objects.all()
    serializer_class = OrganizationMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

class OrganizationRequestViewSet(viewsets.ModelViewSet):
    queryset = OrganizationRequest.objects.all()
    serializer_class = OrganizationRequestSerializer
    permission_classes = [permissions.AllowAny] # Allow public to request

    def perform_create(self, serializer):
        # If user is auth, could link them. For now just save.
        serializer.save()
