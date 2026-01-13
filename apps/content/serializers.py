from rest_framework import serializers
from .models import Announcement, NewsPost

class AnnouncementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.profile.full_name', read_only=True)

    class Meta:
        model = Announcement
        fields = ['id', 'organization', 'title', 'content', 'pinned', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ('created_by',)

class NewsPostSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.profile.full_name', read_only=True)

    class Meta:
        model = NewsPost
        fields = ['id', 'organization', 'title', 'summary', 'content', 'cover_image_url', 'status', 'published_at', 
                  'created_by', 'created_by_name', 'created_at']
        read_only_fields = ('created_by',)
