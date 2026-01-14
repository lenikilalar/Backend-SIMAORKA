from rest_framework import serializers
from .models import Organization, OrganizationMember, OrganizationRequest

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
