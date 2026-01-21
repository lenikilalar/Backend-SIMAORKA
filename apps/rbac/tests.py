"""
Tests for RBAC system.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.rbac.models import Role, Permission, RolePermission, RoleScope


User = get_user_model()


class RoleModelTests(TestCase):
    """Tests for Role model."""
    
    def test_create_system_role(self):
        """Test creating a system-level role."""
        role = Role.objects.create(
            code='TEST_ADMIN',
            name='Test Administrator',
            scope=RoleScope.SYSTEM,
            description='Test system admin role'
        )
        self.assertEqual(role.code, 'TEST_ADMIN')
        self.assertEqual(role.scope, RoleScope.SYSTEM)
        self.assertIn('System', str(role))
    
    def test_create_org_role(self):
        """Test creating an org-level role."""
        role = Role.objects.create(
            code='TEST_ORG_MEMBER',
            name='Test Org Member',
            scope=RoleScope.ORG
        )
        self.assertEqual(role.scope, RoleScope.ORG)


class PermissionModelTests(TestCase):
    """Tests for Permission model."""
    
    def test_create_permission(self):
        """Test creating a permission."""
        perm = Permission.objects.create(
            code='TEST_VIEW',
            name='Test View Permission'
        )
        self.assertEqual(perm.code, 'TEST_VIEW')
        self.assertEqual(str(perm), 'TEST_VIEW')


class RolePermissionTests(TestCase):
    """Tests for role-permission assignments."""
    
    def setUp(self):
        self.role = Role.objects.create(
            code='TEST_ROLE',
            name='Test Role',
            scope=RoleScope.ORG
        )
        self.perm1 = Permission.objects.create(code='PERM_1', name='Permission 1')
        self.perm2 = Permission.objects.create(code='PERM_2', name='Permission 2')
    
    def test_assign_permission_to_role(self):
        """Test assigning permissions to a role."""
        RolePermission.objects.create(role=self.role, permission=self.perm1)
        RolePermission.objects.create(role=self.role, permission=self.perm2)
        
        self.assertEqual(self.role.role_permissions.count(), 2)
    
    def test_unique_together_constraint(self):
        """Test that same permission can't be assigned twice."""
        RolePermission.objects.create(role=self.role, permission=self.perm1)
        
        with self.assertRaises(Exception):
            RolePermission.objects.create(role=self.role, permission=self.perm1)


class SeedRBACCommandTests(TestCase):
    """Tests for seed_rbac management command."""
    
    def test_seed_creates_roles(self):
        """Test that seed command creates expected roles."""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('seed_rbac', stdout=out)
        
        # Check roles were created
        self.assertTrue(Role.objects.filter(code='SUPERADMIN').exists())
        self.assertTrue(Role.objects.filter(code='CAMPUS_ADMIN').exists())
        self.assertTrue(Role.objects.filter(code='ORG_ADMIN').exists())
        self.assertTrue(Role.objects.filter(code='ORG_MEMBER').exists())
    
    def test_seed_creates_permissions(self):
        """Test that seed command creates expected permissions."""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('seed_rbac', stdout=out)
        
        # Check some permissions exist
        self.assertTrue(Permission.objects.filter(code='ORG_VIEW').exists())
        self.assertTrue(Permission.objects.filter(code='ANNOUNCEMENT_CREATE').exists())
        self.assertTrue(Permission.objects.filter(code='FINANCE_VIEW').exists())
    
    def test_seed_is_idempotent(self):
        """Test that running seed twice doesn't duplicate data."""
        from django.core.management import call_command
        from io import StringIO
        
        call_command('seed_rbac', stdout=StringIO())
        first_count = Role.objects.count()
        
        call_command('seed_rbac', stdout=StringIO())
        second_count = Role.objects.count()
        
        self.assertEqual(first_count, second_count)
