"""
Notification views for SIMAORKA API.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from django.utils import timezone

from common.responses import success_response, error_response
from common.exceptions import ErrorCode

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user notifications.
    
    GET /api/v1/notifications - List user's notifications
    GET /api/v1/notifications/{id} - Get notification detail
    POST /api/v1/notifications/{id}/read - Mark notification as read
    POST /api/v1/notifications/read-all - Mark all notifications as read
    DELETE /api/v1/notifications/{id} - Delete notification
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return notifications for the current user."""
        return Notification.objects.filter(user=self.request.user)
    
    def list(self, request):
        """List user's notifications with unread count."""
        queryset = self.get_queryset()
        
        # Filter by read status if provided
        is_read = request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        
        # Filter by type if provided
        notif_type = request.query_params.get('type')
        if notif_type:
            queryset = queryset.filter(type=notif_type)
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        
        # Include unread count in meta
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        
        return success_response(
            serializer.data,
            meta={'unread_count': unread_count}
        )
    
    def retrieve(self, request, pk=None):
        """Get notification detail and mark as read."""
        try:
            notification = self.get_queryset().get(pk=pk)
            
            # Auto-mark as read on retrieve
            if not notification.is_read:
                notification.is_read = True
                notification.read_at = timezone.now()
                notification.save(update_fields=['is_read', 'read_at'])
            
            serializer = self.get_serializer(notification)
            return success_response(serializer.data)
        except Notification.DoesNotExist:
            return error_response(
                ErrorCode.NOT_FOUND,
                "Notification not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        """Mark a single notification as read."""
        try:
            notification = self.get_queryset().get(pk=pk)
            if not notification.is_read:
                notification.is_read = True
                notification.read_at = timezone.now()
                notification.save(update_fields=['is_read', 'read_at'])
            
            return success_response({'message': 'Marked as read'})
        except Notification.DoesNotExist:
            return error_response(
                ErrorCode.NOT_FOUND,
                "Notification not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'], url_path='read-all')
    def read_all(self, request):
        """Mark all user's notifications as read."""
        updated = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        return success_response({
            'message': f'Marked {updated} notifications as read',
            'count': updated
        })
    
    def destroy(self, request, pk=None):
        """Delete a notification."""
        try:
            notification = self.get_queryset().get(pk=pk)
            notification.delete()
            return success_response({'message': 'Notification deleted'})
        except Notification.DoesNotExist:
            return error_response(
                ErrorCode.NOT_FOUND,
                "Notification not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
