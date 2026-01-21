"""
Business logic middleware and utilities for SIMAORKA.
Profile incomplete enforcement, open member window, etc.
"""

from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone

from common.exceptions import ErrorCode


class ProfileIncompleteMiddleware:
    """
    Middleware to enforce profile completion.
    Returns 403 if user profile is incomplete and accessing protected routes.
    """
    
    EXEMPT_PATHS = [
        '/api/v1/auth/',
        '/api/v1/me',
        '/api/v1/uploads/profile-photo',
        '/admin/',
        '/api/schema/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip for unauthenticated or exempt paths
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return self.get_response(request)
        
        # Check if path is exempt
        for exempt in self.EXEMPT_PATHS:
            if request.path.startswith(exempt):
                return self.get_response(request)
        
        # Check profile completeness
        if not self._is_profile_complete(request.user):
            return JsonResponse({
                'error': {
                    'code': ErrorCode.PROFILE_INCOMPLETE,
                    'message': 'Please complete your profile first.',
                    'details': {'redirect': '/profile/complete'}
                }
            }, status=403)
        
        return self.get_response(request)
    
    def _is_profile_complete(self, user):
        """Check if user profile has all required fields."""
        try:
            profile = user.profile
            return all([
                profile.nim,
                profile.full_name,
                profile.faculty,
                profile.major,
                profile.entry_year
            ])
        except Exception:
            return False


def check_open_member_window(organization):
    """
    Check if organization's membership registration is currently open.
    Returns (is_open, message)
    """
    now = timezone.now()
    
    # Check if org has open_member settings
    open_start = getattr(organization, 'open_member_start', None)
    open_end = getattr(organization, 'open_member_end', None)
    
    if open_start is None or open_end is None:
        # No window configured - always open
        return True, "Membership is open"
    
    if open_start <= now <= open_end:
        return True, "Membership registration is open"
    elif now < open_start:
        return False, f"Registration opens on {open_start.strftime('%Y-%m-%d')}"
    else:
        return False, f"Registration closed on {open_end.strftime('%Y-%m-%d')}"


def trigger_announcement_fanout(announcement, organization):
    """
    Send notifications to all active org members when announcement is published.
    """
    from apps.notifications.services import notify_org_members
    from apps.notifications.models import NotificationType
    
    notify_org_members(
        organization=organization,
        title=f"📢 {announcement.title}",
        message=announcement.content[:200] + ('...' if len(announcement.content) > 200 else ''),
        notification_type=NotificationType.ANNOUNCEMENT,
        link=f"/orgs/{organization.slug}/announcements/{announcement.id}",
        exclude_users=[announcement.created_by_id] if announcement.created_by else []
    )


def trigger_event_notification(event, organization, also_announce=False):
    """
    Send notifications for events. If also_announce is True, create an announcement too.
    """
    from apps.notifications.services import notify_org_members
    from apps.notifications.models import NotificationType
    
    # Notify members
    notify_org_members(
        organization=organization,
        title=f"📅 {event.title}",
        message=f"Event on {event.start_at.strftime('%Y-%m-%d %H:%M')}. {event.description[:100]}",
        notification_type=NotificationType.EVENT,
        link=f"/orgs/{organization.slug}/events/{event.id}",
        exclude_users=[event.created_by_id] if event.created_by else []
    )
    
    # Also create announcement if requested
    if also_announce:
        from apps.content.models import Announcement
        Announcement.objects.create(
            organization=organization,
            title=f"📅 Upcoming Event: {event.title}",
            content=f"""
**{event.title}**

📅 Date: {event.start_at.strftime('%Y-%m-%d %H:%M')}
📍 Location: {getattr(event, 'location', 'TBA')}

{event.description}
            """.strip(),
            is_pinned=False,
            created_by=event.created_by
        )
