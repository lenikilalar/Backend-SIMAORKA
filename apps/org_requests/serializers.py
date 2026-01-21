"""OrgRequests serializers for SIMAORKA API."""

from rest_framework import serializers
from .models import OrganizationRequest


class OrgRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationRequest
        fields = '__all__'
        read_only_fields = ['id', 'status', 'admin_note', 'handled_by', 'created_at', 'updated_at']


class OrgRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationRequest
        fields = ['proposed_name', 'proposed_slug', 'proposed_description', 
                  'requester_name', 'requester_email', 'requester_phone']


class OrgRequestReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['approved', 'rejected'])
    admin_note = serializers.CharField(required=False, allow_blank=True)
