from rest_framework import serializers
from .models import DiscussionThread, DiscussionPost, ChatThread, ChatMessage

class DiscussionPostSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.profile.full_name', read_only=True)

    class Meta:
        model = DiscussionPost
        fields = ['id', 'thread', 'content', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ('created_by', 'thread')

class DiscussionThreadSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.profile.full_name', read_only=True)
    post_count = serializers.IntegerField(source='posts.count', read_only=True)

    class Meta:
        model = DiscussionThread
        fields = ['id', 'organization', 'title', 'lock_status', 'created_by', 'created_by_name', 'created_at', 'post_count']
        read_only_fields = ('created_by',)

class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.profile.full_name', read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'thread', 'sender', 'sender_name', 'content', 'sent_at']
        read_only_fields = ('sender',)

class ChatThreadSerializer(serializers.ModelSerializer):
    # This is a basic serializer, real implementation needs participant details
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatThread
        fields = ['id', 'organization', 'type', 'created_at', 'last_message']

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-sent_at').first()
        if last_msg:
            return ChatMessageSerializer(last_msg).data
        return None
