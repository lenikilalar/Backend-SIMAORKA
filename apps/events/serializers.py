from rest_framework import serializers
from .models import Event, EventAttendance

class EventSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.profile.full_name', read_only=True)
    my_status = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = ['id', 'organization', 'title', 'description', 'location', 'start_at', 'end_at', 
                  'is_public', 'max_attendees', 'created_by', 'created_by_name', 'created_at', 'my_status']
        read_only_fields = ('created_by',)

    def get_my_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attendance = obj.attendees.filter(user=request.user).first()
            return attendance.status if attendance else None
        return None

class EventAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventAttendance
        fields = ['event', 'user', 'status', 'marked_at']
        read_only_fields = ('user', 'marked_at')
