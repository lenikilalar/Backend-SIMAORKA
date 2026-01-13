from rest_framework import viewsets, permissions, filters
from django.utils import timezone
from .models import Announcement, NewsPost, PostStatus
from .serializers import AnnouncementSerializer, NewsPostSerializer

class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        org_id = self.request.query_params.get('org_id')
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class NewsPostViewSet(viewsets.ModelViewSet):
    queryset = NewsPost.objects.all()
    serializer_class = NewsPostSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        org_id = self.request.query_params.get('org_id')
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        
        # Public only sees published news
        if self.action in ['list', 'retrieve'] and not self.request.user.is_authenticated:
            queryset = queryset.filter(status=PostStatus.PUBLISHED)
            
        return queryset.order_by('-published_at', '-created_at')

    def perform_create(self, serializer):
        # Auto publish timestamp if published
        status = serializer.validated_data.get('status', PostStatus.DRAFT)
        published_at = None
        if status == PostStatus.PUBLISHED:
            published_at = timezone.now()
            
        serializer.save(created_by=self.request.user, published_at=published_at)
