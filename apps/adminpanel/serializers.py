from rest_framework import serializers

class AdminStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_organizations = serializers.IntegerField()
    active_organizations = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    total_events = serializers.IntegerField()
    total_announcements = serializers.IntegerField()
    users_this_month = serializers.IntegerField()
    orgs_this_month = serializers.IntegerField()
