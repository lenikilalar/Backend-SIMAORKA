"""
Tests for business logic.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import MagicMock, patch
from typing import cast, Any

from common.business import (
    ProfileIncompleteMiddleware,
    check_open_member_window,
    trigger_announcement_fanout
)
from apps.accounts.models import User as UserModel

User = get_user_model()


class ProfileIncompleteMiddlewareTests(TestCase):
    """Tests for profile incomplete enforcement middleware."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = ProfileIncompleteMiddleware(lambda r: r)
        self.user = cast(Any, User.objects).create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_unauthenticated_passes_through(self):
        """Test that unauthenticated requests pass through."""
        request = self.factory.get('/api/v1/orgs/')
        request.user = MagicMock(is_authenticated=False)
        
        response = self.middleware(request)
        self.assertEqual(response, request)
    
    def test_exempt_paths_pass_through(self):
        """Test that exempt paths pass through."""
        request = self.factory.get('/api/v1/auth/login')
        request.user = self.user
        
        response = self.middleware(request)
        self.assertEqual(response, request)
    
    def test_me_endpoint_exempt(self):
        """Test that /me endpoint is exempt."""
        request = self.factory.get('/api/v1/me')
        request.user = self.user
        
        response = self.middleware(request)
        self.assertEqual(response, request)


class OpenMemberWindowTests(TestCase):
    """Tests for open member window logic."""
    
    def test_no_window_configured_always_open(self):
        """Test that orgs without window config are always open."""
        org = MagicMock()
        org.open_member_start = None
        org.open_member_end = None
        
        is_open, message = check_open_member_window(org)
        
        self.assertTrue(is_open)
        self.assertIn('open', message.lower())


class AnnouncementFanoutTests(TestCase):
    """Tests for announcement fanout notifications."""
    
    @patch('common.business.notify_org_members')
    def test_fanout_calls_notify_service(self, mock_notify):
        """Test that fanout triggers notification service."""
        announcement = MagicMock()
        announcement.title = 'Test Announcement'
        announcement.content = 'Test content'
        announcement.id = 'abc123'
        announcement.created_by_id = None
        
        org = MagicMock()
        org.slug = 'test-org'
        
        trigger_announcement_fanout(announcement, org)
        
        mock_notify.assert_called_once()
        call_args = mock_notify.call_args
        self.assertEqual(call_args.kwargs['organization'], org)
        self.assertIn('Test Announcement', call_args.kwargs['title'])
