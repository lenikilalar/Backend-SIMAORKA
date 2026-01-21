"""
Documents serializers for SIMAORKA API.
"""

from rest_framework import serializers
from .models import Document, DocumentVersion, DocumentAccessRule


class DocumentVersionSerializer(serializers.ModelSerializer):
    """Serializer for document versions."""
    uploaded_by_name = serializers.CharField(source='uploaded_by.email', read_only=True)
    
    class Meta:
        model = DocumentVersion
        fields = [
            'id', 'version_number', 'file_path', 'file_hash', 
            'file_size', 'uploaded_by', 'uploaded_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'version_number', 'file_hash', 'created_at']


class DocumentAccessRuleSerializer(serializers.ModelSerializer):
    """Serializer for document access rules."""
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    class Meta:
        model = DocumentAccessRule
        fields = ['id', 'role', 'role_name', 'can_view', 'can_edit', 'can_approve']


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for documents list/detail."""
    latest_version = serializers.SerializerMethodField()
    version_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.email', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'organization', 'title', 'description', 'status',
            'requires_nft', 'required_role_code',
            'latest_version', 'version_count',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_latest_version(self, obj):
        version = obj.versions.first()
        if version:
            return DocumentVersionSerializer(version).data
        return None
    
    def get_version_count(self, obj):
        return obj.versions.count()


class DocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating documents."""
    
    class Meta:
        model = Document
        fields = [
            'organization', 'title', 'description', 'status',
            'requires_nft', 'required_role_code'
        ]
