"""
Documents models for SIMAORKA.
Supports versioning and access control.
"""

from django.db import models
from django.conf import settings
import uuid


class DocumentStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PUBLISHED = 'published', 'Published'
    ARCHIVED = 'archived', 'Archived'


class Document(models.Model):
    """Organization document."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='documents')
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.DRAFT)
    
    # Web3 gating (optional)
    requires_nft = models.BooleanField(default=False)
    required_role_code = models.CharField(max_length=100, blank=True)  # Role NFT code required
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_documents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'documents'

    def __str__(self):
        return self.title


class DocumentVersion(models.Model):
    """Version history for documents."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    
    version_number = models.PositiveIntegerField()
    file_path = models.TextField()  # Storage path
    file_hash = models.CharField(max_length=64)  # SHA256 hash for integrity
    file_size = models.PositiveIntegerField()
    
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'document_versions'
        unique_together = ('document', 'version_number')
        ordering = ['-version_number']

    def __str__(self):
        return f"{self.document.title} v{self.version_number}"


class DocumentAccessRule(models.Model):
    """Access control rules for documents."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='access_rules')
    role = models.ForeignKey('rbac.Role', on_delete=models.CASCADE)
    can_view = models.BooleanField(default=True)
    can_edit = models.BooleanField(default=False)
    can_approve = models.BooleanField(default=False)

    class Meta:
        db_table = 'document_access_rules'
        unique_together = ('document', 'role')
