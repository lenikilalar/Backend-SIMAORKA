"""
Notification service for fanout and utility functions.
"""

from django.db import transaction
from .models import Notification, NotificationType


def send_notification(user, title, message, notification_type=NotificationType.SYSTEM, 
                      organization=None, link=''):
    """
    Send a single notification to a user.
    
    Args:
        user: User instance to notify
        title: Notification title
        message: Notification message body
        notification_type: One of NotificationType choices
        organization: Optional organization context
        link: Optional frontend route link
    
    Returns:
        Notification instance
    """
    return Notification.objects.create(
        user=user,
        organization=organization,
        type=notification_type,
        title=title,
        message=message,
        link=link
    )


def fanout_notification(users, title, message, notification_type=NotificationType.SYSTEM,
                        organization=None, link=''):
    """
    Send the same notification to multiple users (fanout).
    
    Args:
        users: QuerySet or list of User instances
        title: Notification title
        message: Notification message body
        notification_type: One of NotificationType choices
        organization: Optional organization context
        link: Optional frontend route link
    
    Returns:
        Number of notifications created
    """
    notifications = []
    for user in users:
        notifications.append(Notification(
            user=user,
            organization=organization,
            type=notification_type,
            title=title,
            message=message,
            link=link
        ))
    
    with transaction.atomic():
        Notification.objects.bulk_create(notifications)
    
    return len(notifications)


def notify_org_members(organization, title, message, notification_type=NotificationType.ANNOUNCEMENT,
                       link='', exclude_users=None):
    """
    Send notification to all active members of an organization.
    
    Args:
        organization: Organization instance
        title: Notification title
        message: Notification message body
        notification_type: One of NotificationType choices
        link: Optional frontend route link
        exclude_users: Optional list of user IDs to exclude
    
    Returns:
        Number of notifications created
    """
    from apps.organizations.models import OrganizationMember, MembershipStatus
    
    members = OrganizationMember.objects.filter(
        organization=organization,
        status=MembershipStatus.ACTIVE
    ).select_related('user')
    
    if exclude_users:
        members = members.exclude(user_id__in=exclude_users)
    
    users = [m.user for m in members]
    
    return fanout_notification(
        users=users,
        title=title,
        message=message,
        notification_type=notification_type,
        organization=organization,
        link=link
    )
