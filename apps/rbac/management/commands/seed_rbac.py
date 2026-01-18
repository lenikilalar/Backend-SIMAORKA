"""
Management command to seed RBAC roles and permissions.
Usage: python manage.py seed_rbac
"""

from django.core.management.base import BaseCommand
from apps.rbac.models import Role, Permission, RolePermission, RoleScope


# Define all permissions per TSD V2
PERMISSIONS = [
    # Organization
    ('ORG_VIEW', 'View Organization'),
    ('ORG_EDIT', 'Edit Organization'),
    ('ORG_MANAGE_MEMBERS', 'Manage Organization Members'),
    ('ORG_MANAGE_ROLES', 'Manage Organization Roles'),
    
    # Announcements
    ('ANNOUNCEMENT_VIEW', 'View Announcements'),
    ('ANNOUNCEMENT_CREATE', 'Create Announcement'),
    ('ANNOUNCEMENT_EDIT', 'Edit Announcement'),
    ('ANNOUNCEMENT_DELETE', 'Delete Announcement'),
    
    # Events
    ('EVENT_VIEW', 'View Events'),
    ('EVENT_CREATE', 'Create Event'),
    ('EVENT_EDIT', 'Edit Event'),
    ('EVENT_DELETE', 'Delete Event'),
    
    # News
    ('NEWS_VIEW', 'View News'),
    ('NEWS_CREATE', 'Create News'),
    ('NEWS_EDIT', 'Edit News'),
    ('NEWS_DELETE', 'Delete News'),
    
    # Finance
    ('FINANCE_VIEW', 'View Finance'),
    ('FINANCE_CREATE', 'Create Finance Transaction'),
    ('FINANCE_EDIT', 'Edit Finance Transaction'),
    ('FINANCE_EXPORT', 'Export Finance Data'),
    
    # Documents
    ('DOCUMENT_VIEW', 'View Documents'),
    ('DOCUMENT_CREATE', 'Create Document'),
    ('DOCUMENT_EDIT', 'Edit Document'),
    ('DOCUMENT_DELETE', 'Delete Document'),
    
    # Voting
    ('VOTE_VIEW', 'View Voting Sessions'),
    ('VOTE_CREATE', 'Create Voting Session'),
    ('VOTE_MANAGE', 'Manage Voting Sessions'),
    ('VOTE_CAST', 'Cast Vote'),
    
    # Discussions
    ('DISCUSSION_VIEW', 'View Discussions'),
    ('DISCUSSION_CREATE', 'Create Discussion'),
    ('DISCUSSION_MODERATE', 'Moderate Discussions'),
    
    # Chat
    ('CHAT_VIEW', 'View Chat'),
    ('CHAT_SEND', 'Send Chat Messages'),
    
    # Web3
    ('WEB3_VIEW', 'View Web3 Info'),
    ('WEB3_MINT_NFT', 'Mint Role NFT'),
    ('WEB3_REVOKE_NFT', 'Revoke Role NFT'),
    
    # Admin
    ('ADMIN_VIEW_AUDIT', 'View Audit Logs'),
    ('ADMIN_MANAGE_ORGS', 'Manage All Organizations'),
    ('ADMIN_MANAGE_USERS', 'Manage All Users'),
]

# Define roles with their scopes and permissions
ROLES = {
    # System-level roles
    'SUPERADMIN': {
        'name': 'Super Administrator',
        'scope': RoleScope.SYSTEM,
        'description': 'Full system access',
        'permissions': ['*']  # All permissions
    },
    'CAMPUS_ADMIN': {
        'name': 'Campus Administrator',
        'scope': RoleScope.SYSTEM,
        'description': 'Campus-wide administration',
        'permissions': [
            'ADMIN_VIEW_AUDIT', 'ADMIN_MANAGE_ORGS', 'ORG_VIEW', 
            'ORG_MANAGE_MEMBERS', 'ANNOUNCEMENT_VIEW', 'EVENT_VIEW',
            'NEWS_VIEW', 'FINANCE_VIEW'
        ]
    },
    
    # Org-level roles
    'ORG_ADMIN': {
        'name': 'Organization Admin',
        'scope': RoleScope.ORG,
        'description': 'Full organization management',
        'permissions': [
            'ORG_VIEW', 'ORG_EDIT', 'ORG_MANAGE_MEMBERS', 'ORG_MANAGE_ROLES',
            'ANNOUNCEMENT_VIEW', 'ANNOUNCEMENT_CREATE', 'ANNOUNCEMENT_EDIT', 'ANNOUNCEMENT_DELETE',
            'EVENT_VIEW', 'EVENT_CREATE', 'EVENT_EDIT', 'EVENT_DELETE',
            'NEWS_VIEW', 'NEWS_CREATE', 'NEWS_EDIT', 'NEWS_DELETE',
            'FINANCE_VIEW', 'FINANCE_CREATE', 'FINANCE_EDIT', 'FINANCE_EXPORT',
            'DOCUMENT_VIEW', 'DOCUMENT_CREATE', 'DOCUMENT_EDIT', 'DOCUMENT_DELETE',
            'VOTE_VIEW', 'VOTE_CREATE', 'VOTE_MANAGE', 'VOTE_CAST',
            'DISCUSSION_VIEW', 'DISCUSSION_CREATE', 'DISCUSSION_MODERATE',
            'CHAT_VIEW', 'CHAT_SEND',
            'WEB3_VIEW', 'WEB3_MINT_NFT', 'WEB3_REVOKE_NFT'
        ]
    },
    'ORG_SECRETARY': {
        'name': 'Organization Secretary',
        'scope': RoleScope.ORG,
        'description': 'Manages announcements, events, and documents',
        'permissions': [
            'ORG_VIEW',
            'ANNOUNCEMENT_VIEW', 'ANNOUNCEMENT_CREATE', 'ANNOUNCEMENT_EDIT',
            'EVENT_VIEW', 'EVENT_CREATE', 'EVENT_EDIT',
            'NEWS_VIEW', 'NEWS_CREATE', 'NEWS_EDIT',
            'DOCUMENT_VIEW', 'DOCUMENT_CREATE', 'DOCUMENT_EDIT',
            'DISCUSSION_VIEW', 'DISCUSSION_CREATE',
            'CHAT_VIEW', 'CHAT_SEND'
        ]
    },
    'ORG_TREASURER': {
        'name': 'Organization Treasurer',
        'scope': RoleScope.ORG,
        'description': 'Manages finance and transactions',
        'permissions': [
            'ORG_VIEW',
            'FINANCE_VIEW', 'FINANCE_CREATE', 'FINANCE_EDIT', 'FINANCE_EXPORT',
            'DOCUMENT_VIEW',
            'CHAT_VIEW', 'CHAT_SEND'
        ]
    },
    'ORG_MEMBER': {
        'name': 'Organization Member',
        'scope': RoleScope.ORG,
        'description': 'Basic member access',
        'permissions': [
            'ORG_VIEW',
            'ANNOUNCEMENT_VIEW',
            'EVENT_VIEW',
            'NEWS_VIEW',
            'FINANCE_VIEW',
            'DOCUMENT_VIEW',
            'VOTE_VIEW', 'VOTE_CAST',
            'DISCUSSION_VIEW', 'DISCUSSION_CREATE',
            'CHAT_VIEW', 'CHAT_SEND',
            'WEB3_VIEW'
        ]
    },
}


class Command(BaseCommand):
    help = 'Seeds the database with default roles and permissions'

    def handle(self, *args, **options):
        self.stdout.write('Seeding RBAC data...')
        
        # Create permissions
        permission_objects = {}
        for code, name in PERMISSIONS:
            perm, created = Permission.objects.update_or_create(
                code=code,
                defaults={'name': name, 'description': f'{name} permission'}
            )
            permission_objects[code] = perm
            if created:
                self.stdout.write(f'  Created permission: {code}')
        
        self.stdout.write(self.style.SUCCESS(f'  Total permissions: {len(permission_objects)}'))
        
        # Create roles
        for role_code, role_data in ROLES.items():
            role, created = Role.objects.update_or_create(
                code=role_code,
                defaults={
                    'name': role_data['name'],
                    'scope': role_data['scope'],
                    'description': role_data['description']
                }
            )
            
            if created:
                self.stdout.write(f'  Created role: {role_code}')
            
            # Assign permissions
            role_perms = role_data['permissions']
            if role_perms == ['*']:
                # All permissions
                perms_to_assign = permission_objects.values()
            else:
                perms_to_assign = [permission_objects[p] for p in role_perms if p in permission_objects]
            
            # Clear existing and add new
            RolePermission.objects.filter(role=role).delete()
            for perm in perms_to_assign:
                RolePermission.objects.create(role=role, permission=perm)
            
            self.stdout.write(f'    Assigned {len(list(perms_to_assign))} permissions to {role_code}')
        
        self.stdout.write(self.style.SUCCESS('RBAC seeding complete!'))
