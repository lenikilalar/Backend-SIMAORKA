"""
Organization Request models for SIMAORKA.
Handles new organization creation requests.
"""

from django.db import models
from django.conf import settings
import uuid


class OrgRequestStatus(models.TextChoices):
    SUBMITTED = 'submitted', 'Submitted'
    IN_REVIEW = 'in_review', 'In Review'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'


class OrganizationRequest(models.Model):
    """Request to create a new organization."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    proposed_name = models.CharField(max_length=255)
    proposed_slug = models.SlugField(max_length=255, blank=True)
    proposed_description = models.TextField(blank=True)
    
    requester_name = models.CharField(max_length=255)
    requester_email = models.EmailField()
    requester_phone = models.CharField(max_length=50, blank=True)
    requester_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='org_requests')
    
    status = models.CharField(max_length=20, choices=OrgRequestStatus.choices, default=OrgRequestStatus.SUBMITTED)
    admin_note = models.TextField(blank=True)
    handled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_org_requests')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organization_requests'

    def __str__(self):
        return f"Request: {self.proposed_name} ({self.status})"
