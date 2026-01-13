from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid

# Enums
class OrgStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    ACTIVE = 'active', 'Active'
    SUSPENDED = 'suspended', 'Suspended'

class RoleScope(models.TextChoices):
    SYSTEM = 'SYSTEM', 'System'
    ORG = 'ORG', 'Organization'

class MembershipStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    ACTIVE = 'active', 'Active'
    REJECTED = 'rejected', 'Rejected'
    REMOVED = 'removed', 'Removed'

class OrgRequestStatus(models.TextChoices):
    SUBMITTED = 'submitted', 'Submitted'
    IN_REVIEW = 'in_review', 'In Review'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    vision = models.TextField(null=True, blank=True)
    mission = models.TextField(null=True, blank=True)
    
    contact_email = models.EmailField(null=True, blank=True)
    contact_phone = models.CharField(max_length=50, null=True, blank=True)
    contact_socials = models.JSONField(null=True, blank=True) # Renamed from contact_socials_json
    
    logo_url = models.TextField(null=True, blank=True)
    
    is_private = models.BooleanField(default=False)
    open_member = models.BooleanField(default=False)
    open_member_start_at = models.DateTimeField(null=True, blank=True)
    open_member_end_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=OrgStatus.choices, default=OrgStatus.DRAFT)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_orgs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organizations'

    def __str__(self):
        return self.name

class Role(models.Model):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    scope = models.CharField(max_length=20, choices=RoleScope.choices)

    class Meta:
        db_table = 'roles'

    def __str__(self):
        return self.name

class Permission(models.Model):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'permissions'

    def __str__(self):
        return self.name

class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        db_table = 'role_permissions'
        unique_together = ('role', 'permission')

class OrganizationMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    status = models.CharField(max_length=20, choices=MembershipStatus.choices, default=MembershipStatus.PENDING)
    
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'organization_members'
        unique_together = ('organization', 'user')

    def __str__(self):
        return f"{self.user} in {self.organization}"

class MemberRole(models.Model):
    member = models.ForeignKey(OrganizationMember, on_delete=models.CASCADE, related_name='roles')
    role = models.ForeignKey(Role, on_delete=models.RESTRICT)

    class Meta:
        db_table = 'member_roles'
        unique_together = ('member', 'role')

class OrganizationPosition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='positions')
    name = models.CharField(max_length=255)
    rank = models.IntegerField(default=0)
    is_core = models.BooleanField(default=True)

    class Meta:
        db_table = 'organization_positions'

    def __str__(self):
        return f"{self.name} at {self.organization}"

class MemberPosition(models.Model):
    member = models.ForeignKey(OrganizationMember, on_delete=models.CASCADE, related_name='positions')
    position = models.ForeignKey(OrganizationPosition, on_delete=models.CASCADE)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'member_positions'

class OrganizationRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proposed_name = models.CharField(max_length=255)
    proposed_description = models.TextField(null=True, blank=True)
    requester_name = models.CharField(max_length=255)
    requester_email = models.EmailField()
    requester_phone = models.CharField(max_length=50, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=OrgRequestStatus.choices, default=OrgRequestStatus.SUBMITTED)
    admin_note = models.TextField(null=True, blank=True)
    handled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_org_requests')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organization_requests'
