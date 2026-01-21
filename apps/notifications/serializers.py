"""
Notification serializers for SIMAORKA API.
"""

from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notification list and detail."""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'message', 'link',
            'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications (internal use)."""
    
    class Meta:
        model = Notification
        fields = [
            'user', 'organization', 'type', 'title', 'message', 'link'
        ]
