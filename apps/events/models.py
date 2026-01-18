from django.db import models
from django.conf import settings
import uuid

class AttendanceStatus(models.TextChoices):
    GOING = 'going', 'Going'
    INTERESTED = 'interested', 'Interested'
    NOT_GOING = 'not_going', 'Not Going'

class ReminderChannel(models.TextChoices):
    IN_APP = 'in_app', 'In App'
    EMAIL = 'email', 'Email'

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    is_public = models.BooleanField(default=False)
    max_attendees = models.PositiveIntegerField(null=True, blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_events')
    linked_announcement = models.ForeignKey('content.Announcement', on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_event')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'events'

    def __str__(self):
        return self.title

class EventAttendance(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendees')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_attendance')
    status = models.CharField(max_length=20, choices=AttendanceStatus.choices, default=AttendanceStatus.INTERESTED)
    marked_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'event_attendance'
        unique_together = ('event', 'user')

class EventReminder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reminders')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_reminders')
    remind_at = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    channel = models.CharField(max_length=20, choices=ReminderChannel.choices, default=ReminderChannel.IN_APP)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'event_reminders'
        unique_together = ('event', 'user', 'remind_at')
