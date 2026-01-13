from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import StudentProfile

User = get_user_model()

class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ['nim', 'full_name', 'faculty', 'major', 'entry_year', 'profile_photo_url']

class UserSerializer(serializers.ModelSerializer):
    profile = StudentProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'is_staff', 'is_active', 'profile']

class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField(required=True)
