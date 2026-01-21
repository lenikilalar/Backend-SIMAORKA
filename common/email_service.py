"""
Email service for SIMAORKA.
Handles sending transactional emails with templates.
"""

import secrets
from datetime import timedelta
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags


def generate_reset_token():
    """Generate a secure random token for password reset."""
    return secrets.token_urlsafe(48)


def create_password_reset_token(user):
    """Create a password reset token for user."""
    from apps.accounts.models import PasswordResetToken
    
    # Invalidate existing tokens
    PasswordResetToken.objects.filter(user=user, used_at__isnull=True).update(
        used_at=timezone.now()
    )
    
    # Create new token
    token = PasswordResetToken.objects.create(
        user=user,
        token=generate_reset_token(),
        expires_at=timezone.now() + timedelta(hours=1)
    )
    
    return token


def get_frontend_url():
    """Get frontend URL from settings."""
    return getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')


def send_email(to_email, subject, template_name, context, from_email=None):
    """
    Send an HTML email with plain text fallback.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        template_name: Template name without extension (e.g., 'password_reset')
        context: Template context dict
        from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
    
    Returns:
        bool: Success status
    """
    if from_email is None:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@simaorka.id')
    
    # Add common context
    context['frontend_url'] = get_frontend_url()
    context['current_year'] = timezone.now().year
    
    try:
        # Render HTML template
        html_content = render_to_string(f'emails/{template_name}.html', context)
        text_content = strip_tags(html_content)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[to_email]
        )
        email.attach_alternative(html_content, 'text/html')
        
        # Send
        email.send(fail_silently=False)
        return True
        
    except Exception as e:
        # Log error in production
        print(f"Email send error: {e}")
        return False


def send_password_reset_email(user):
    """
    Send password reset email to user.
    
    Returns:
        (bool, token): Success status and token object
    """
    token = create_password_reset_token(user)
    reset_url = f"{get_frontend_url()}/auth/reset-password?token={token.token}"
    
    context = {
        'user': user,
        'reset_url': reset_url,
        'expires_hours': 1,
    }
    
    success = send_email(
        to_email=user.email,
        subject='Reset Password SIMAORKA',
        template_name='password_reset',
        context=context
    )
    
    return success, token


def send_welcome_email(user):
    """Send welcome email to new user."""
    context = {
        'user': user,
        'login_url': f"{get_frontend_url()}/auth/login",
    }
    
    return send_email(
        to_email=user.email,
        subject='Selamat Datang di SIMAORKA',
        template_name='welcome',
        context=context
    )


def send_notification_email(user, notification):
    """
    Send notification via email.
    Checks user preferences before sending.
    """
    from apps.accounts.models import EmailPreference
    
    # Check user preferences
    try:
        prefs = user.email_preferences
        if not prefs.should_send_email(notification.type):
            return False
    except EmailPreference.DoesNotExist:
        # No preferences = use defaults (send email)
        pass
    
    context = {
        'user': user,
        'notification': notification,
        'view_url': f"{get_frontend_url()}{notification.link}" if notification.link else None,
    }
    
    return send_email(
        to_email=user.email,
        subject=f"[SIMAORKA] {notification.title}",
        template_name='notification',
        context=context
    )


def send_payment_confirmation_email(user, payment):
    """Send payment confirmation email."""
    context = {
        'user': user,
        'payment': payment,
        'amount': payment.amount,
        'tx_hash': payment.tx_hash,
        'confirmed_at': payment.confirmed_at,
    }
    
    return send_email(
        to_email=user.email,
        subject='Pembayaran SIMAORKA Berhasil Diverifikasi',
        template_name='payment_confirmed',
        context=context
    )


def send_org_invite_email(user, organization, inviter):
    """Send organization invitation email."""
    context = {
        'user': user,
        'organization': organization,
        'inviter': inviter,
        'accept_url': f"{get_frontend_url()}/orgs/{organization.slug}/join",
    }
    
    return send_email(
        to_email=user.email,
        subject=f'Undangan Bergabung ke {organization.name}',
        template_name='org_invite',
        context=context
    )


def send_event_reminder_email(user, event):
    """Send event reminder email."""
    context = {
        'user': user,
        'event': event,
        'event_url': f"{get_frontend_url()}/events/{event.id}",
    }
    
    return send_email(
        to_email=user.email,
        subject=f'Pengingat: {event.title}',
        template_name='event_reminder',
        context=context
    )
