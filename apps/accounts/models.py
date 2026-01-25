from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid
from typing import Any, ClassVar

class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields: Any) -> Any:
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields: Any) -> Any:
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    id: Any = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    google_sub = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects: ClassVar[UserManager] = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'users'

    def __str__(self):
        return self.email

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='profile')
    nim = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=255)
    faculty = models.CharField(max_length=100)
    major = models.CharField(max_length=100)
    entry_year = models.PositiveIntegerField()
    
    profile_photo_url = models.TextField(null=True, blank=True)
    avatar_bg_color = models.CharField(max_length=20, null=True, blank=True)
    avatar_initials = models.CharField(max_length=10, null=True, blank=True)
    mini_photo_url = models.TextField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student_profiles'

    def __str__(self):
        return f"{self.full_name} ({self.nim})"


class DigestFrequency(models.TextChoices):
    INSTANT = 'instant', 'Instant'
    DAILY = 'daily', 'Daily Digest'
    WEEKLY = 'weekly', 'Weekly Digest'
    NONE = 'none', 'No Email'


class EmailPreference(models.Model):
    """User email notification preferences."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='email_preferences')
    
    # Notification type toggles
    receive_announcements = models.BooleanField(default=True, help_text='Receive org announcements via email')
    receive_events = models.BooleanField(default=True, help_text='Receive event reminders via email')
    receive_finance = models.BooleanField(default=True, help_text='Receive payment confirmations via email')
    receive_applications = models.BooleanField(default=True, help_text='Receive membership updates via email')
    receive_system = models.BooleanField(default=True, help_text='Receive system notifications via email')
    
    # Digest settings
    digest_frequency = models.CharField(
        max_length=20, 
        choices=DigestFrequency.choices, 
        default=DigestFrequency.INSTANT,
        help_text='How often to receive email digests'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'email_preferences'

    def __str__(self):
        return f"Email prefs for {self.user.email}"
    
    def should_send_email(self, notification_type):
        """Check if user wants to receive this notification type via email."""
        if self.digest_frequency == DigestFrequency.NONE:
            return False
        
        type_map = {
            'announcement': self.receive_announcements,
            'event': self.receive_events,
            'finance': self.receive_finance,
            'application': self.receive_applications,
            'system': self.receive_system,
        }
        return type_map.get(notification_type, True)


class PasswordResetToken(models.Model):
    """Token for password reset requests."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'password_reset_tokens'

    def __str__(self):
        return f"Reset token for {self.user.email}"
    
    @property
    def is_valid(self):
        from django.utils import timezone
        return self.used_at is None and self.expires_at > timezone.now()

