from rest_framework import viewsets, permissions, filters
from rest_framework.request import Request
from django.utils import timezone
from .models import Announcement, NewsPost, PostStatus
from .serializers import AnnouncementSerializer, NewsPostSerializer
from drf_spectacular.utils import extend_schema
from typing import cast, Any

@extend_schema(tags=['Announcements'])
class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes: Any = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        request = cast(Request, self.request)
        org_id = request.query_params.get('org_id')
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

@extend_schema(tags=['News'])
class NewsPostViewSet(viewsets.ModelViewSet):
    queryset = NewsPost.objects.all()
    serializer_class = NewsPostSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def list(self, request: Request, *args: Any, **kwargs: Any):
        queryset = self.filter_queryset(self.get_queryset())
        
        category = request.query_params.get('category')
        org_id = request.query_params.get('org_id')
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        
        # Public only sees published news
        if self.action in ['list', 'retrieve'] and not self.request.user.is_authenticated:
            queryset = queryset.filter(status=PostStatus.PUBLISHED)
            
        queryset = queryset.order_by('-published_at', '-created_at')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        from rest_framework.response import Response
        return Response(serializer.data)

    def get_queryset(self):
        queryset = super().get_queryset()
        request = cast(Request, self.request)
        org_id = request.query_params.get('org_id')
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
