"""
Notifications models for SIMAORKA.
"""

from django.db import models
from django.conf import settings
import uuid


class NotificationType(models.TextChoices):
    ANNOUNCEMENT = 'announcement', 'Announcement'
    EVENT = 'event', 'Event'
    APPLICATION = 'application', 'Application'
    FINANCE = 'finance', 'Finance'
    SYSTEM = 'system', 'System'


class Notification(models.Model):
    """User notification."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    type = models.CharField(max_length=50, choices=NotificationType.choices, default=NotificationType.SYSTEM)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.TextField(blank=True)  # Frontend route to navigate
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type}: {self.title}"
