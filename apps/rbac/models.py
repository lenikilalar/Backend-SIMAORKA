"""
RBAC Models for SIMAORKA.
Roles, Permissions, and their relationships.
"""

from django.db import models


class RoleScope(models.TextChoices):
    SYSTEM = 'SYSTEM', 'System'
    ORG = 'ORG', 'Organization'


class Role(models.Model):
    """Role definition (can be system-wide or org-specific)."""
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    scope = models.CharField(max_length=20, choices=RoleScope.choices)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'roles'

    def __str__(self):
        return f"{self.name} ({self.scope})"


class Permission(models.Model):
    """Permission definition."""
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'permissions'

    def __str__(self):
        return self.code


class RolePermission(models.Model):
    """Many-to-many relationship between roles and permissions."""
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='permission_roles')

    class Meta:
        db_table = 'role_permissions'
        unique_together = ('role', 'permission')

    def __str__(self):
        return f"{self.role.code} -> {self.permission.code}"
