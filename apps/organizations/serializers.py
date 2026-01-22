from rest_framework import serializers
from .models import Organization, OrganizationMember
from apps.org_requests.models import OrganizationRequest

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'
        read_only_fields = ('created_by', 'slug', 'status') # Slug auto-generated usually, status draft initially

class OrganizationMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.profile.full_name', read_only=True)

    class Meta:
        model = OrganizationMember
        fields = ['id', 'organization', 'user', 'user_email', 'user_name', 'status', 'joined_at', 'created_at']

class OrganizationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationRequest # Need to import this
        fields = '__all__'
        read_only_fields = ('status', 'admin_note', 'handled_by')

class PublicOrganizationSerializer(serializers.ModelSerializer):
    is_open_for_recruitment = serializers.BooleanField(source='open_member')
    short_description = serializers.CharField(source='description', allow_null=True)
    member_count = serializers.IntegerField(read_only=True)
    category = serializers.CharField(default='General') # specific category field missing in model

    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug', 'logo_url', 'category', 'short_description', 'member_count', 'is_open_for_recruitment']

