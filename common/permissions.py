"""
RBAC Permission classes for SIMAORKA API.
"""

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from typing import Any


class IsSystemAdmin(permissions.BasePermission):
    """
    Permission check for system-level admins (CAMPUS_ADMIN, SUPERADMIN).
    """
    message = "System admin access required."

    def has_permission(self, request: Any, view: Any) -> Any:
        if not request.user.is_authenticated:
            return False
            
        # Superuser always has system access
        if request.user.is_superuser:
            return True
        
        # Check for system roles via member_roles with SYSTEM scope
        from apps.organizations.models import MemberRole
        from apps.rbac.models import RoleScope
        
        system_roles = ['CAMPUS_ADMIN', 'SUPERADMIN']
        return MemberRole.objects.filter(
            member__user=request.user,
            role__code__in=system_roles,
            role__scope=RoleScope.SYSTEM
        ).exists()


class IsOrgMemberActive(permissions.BasePermission):
    """
    Permission check for active organization members.
    Requires 'org_id' or 'slug' in view kwargs.
    """
    message = "Active organization membership required."

    def has_permission(self, request: Any, view: Any) -> Any:
        if not request.user.is_authenticated:
            return False
        
        from apps.organizations.models import OrganizationMember, MembershipStatus
        
        org_id = view.kwargs.get('org_id') or view.kwargs.get('pk')
        slug = view.kwargs.get('slug')
        
        if not org_id and not slug:
            return False
        
        filter_kwargs = {'user': request.user, 'status': MembershipStatus.ACTIVE}
        if org_id:
            filter_kwargs['organization_id'] = org_id
        elif slug:
            filter_kwargs['organization__slug'] = slug
        
        return OrganizationMember.objects.filter(**filter_kwargs).exists()


class HasOrgPermission(permissions.BasePermission):
    """
    Permission check for specific org-level permissions.
    Usage: HasOrgPermission('ANNOUNCEMENT_CREATE', org_kwarg='org_id')
    """

    def __init__(self, permission_code, org_kwarg='org_id'):
        self.permission_code = permission_code
        self.org_kwarg = org_kwarg

    def has_permission(self, request: Any, view: Any) -> Any:
        if not request.user.is_authenticated:
            return False
        
        from apps.organizations.models import OrganizationMember, MemberRole, MembershipStatus
        from apps.rbac.models import RolePermission
        
        org_id = view.kwargs.get(self.org_kwarg) or view.kwargs.get('pk')
        if not org_id:
            return False
        
        # Find active membership
        try:
            member = OrganizationMember.objects.get(
                organization_id=org_id,
                user=request.user,
                status=MembershipStatus.ACTIVE
            )
        except OrganizationMember.DoesNotExist:
            return False
        
        # Check if any of user's roles have the required permission
        member_role_ids = MemberRole.objects.filter(member=member).values_list('role_id', flat=True)
        
        return RolePermission.objects.filter(
            role_id__in=member_role_ids,
            permission__code=self.permission_code
        ).exists()


def has_org_permission_factory(permission_code, org_kwarg='org_id'):
    """
    Factory function to create permission class instances.
    Use this in ViewSets: permission_classes = [has_org_permission_factory('ANNOUNCEMENT_CREATE')]
    """
    class DynamicHasOrgPermission(HasOrgPermission):
        def __init__(self):
            super().__init__(permission_code, org_kwarg)
    
    return DynamicHasOrgPermission
