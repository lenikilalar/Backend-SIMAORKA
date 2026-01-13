from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.text import slugify
from .models import Organization, OrganizationMember
from .serializers import OrganizationSerializer, OrganizationMemberSerializer

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'slug']
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'news', 'events']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        # Auto slugify
        name = serializer.validated_data.get('name')
        slug = slugify(name)
        # Handle duplicate slugs (simple append)
        if Organization.objects.filter(slug=slug).exists():
            import uuid
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"
        
        serializer.save(created_by=self.request.user, slug=slug)

    @action(detail=True, methods=['get'])
    def members(self, request, slug=None):
        org = self.get_object()
        members = org.members.all()
        serializer = OrganizationMemberSerializer(members, many=True)
        return Response(serializer.data)

class OrganizationMemberViewSet(viewsets.ModelViewSet):
    queryset = OrganizationMember.objects.all()
    serializer_class = OrganizationMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter by org if provided in query params or url logic
        # For simplicity, assume nested logic or just standard ID access
        return super().get_queryset()
