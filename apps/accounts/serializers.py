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

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    full_name = serializers.CharField(max_length=255, required=True)
    nim = serializers.CharField(max_length=50, required=True)
    faculty = serializers.CharField(max_length=100, required=True)
    major = serializers.CharField(max_length=100, required=True)
    entry_year = serializers.IntegerField(required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'full_name', 'nim', 'faculty', 'major', 'entry_year']

    def create(self, validated_data):
        # Extract profile data
        profile_data = {
            'full_name': validated_data.pop('full_name'),
            'nim': validated_data.pop('nim'),
            'faculty': validated_data.pop('faculty'),
            'major': validated_data.pop('major'),
            'entry_year': validated_data.pop('entry_year')
        }
        
        # Create User
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        # Create Profile
        StudentProfile.objects.create(user=user, **profile_data)
        
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
