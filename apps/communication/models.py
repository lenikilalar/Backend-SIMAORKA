from django.db import models
from django.conf import settings
import uuid

class DiscussionLockStatus(models.TextChoices):
    OPEN = 'open', 'Open'
    LOCKED = 'locked', 'Locked'

class ChatThreadType(models.TextChoices):
    DIRECT = 'direct', 'Direct'

class DiscussionThread(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='discussions')
    title = models.CharField(max_length=255)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_discussions')
    lock_status = models.CharField(max_length=20, choices=DiscussionLockStatus.choices, default=DiscussionLockStatus.OPEN)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'discussion_threads'

    def __str__(self):
        return self.title

class DiscussionPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(DiscussionThread, on_delete=models.CASCADE, related_name='posts')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='discussion_posts')
    content = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'discussion_posts'

class ChatThread(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='chats')
    type = models.CharField(max_length=20, choices=ChatThreadType.choices, default=ChatThreadType.DIRECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_threads'

class ChatParticipant(models.Model):
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_participations')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_participants'
        unique_together = ('thread', 'user')

class ChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'chat_messages'
