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
    id_token = serializers.CharField(required=False)
    token = serializers.CharField(required=False)

    def validate(self, attrs):
        token = attrs.get('token') or attrs.get('id_token')
        if not token:
            raise serializers.ValidationError({"token": "Token is required."})
        attrs['id_token'] = token
        return attrs


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


class MembershipSerializer(serializers.Serializer):
    """Serializer for organization memberships in /me endpoint."""
    org_id = serializers.UUIDField(source='organization.id')
    org_name = serializers.CharField(source='organization.name')
    org_slug = serializers.CharField(source='organization.slug')
    status = serializers.CharField()
    roles = serializers.SerializerMethodField()

    def get_roles(self, obj):
        return list(obj.roles.values_list('role__code', flat=True))


class UserMeSerializer(serializers.ModelSerializer):
    """Enhanced serializer for GET /me endpoint per TSD V2."""
    profile = StudentProfileSerializer(read_only=True)
    profile_complete = serializers.SerializerMethodField()
    memberships = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'is_staff', 'is_active', 'profile', 'profile_complete', 'memberships']
    
    def get_profile_complete(self, obj):
        """Check if user profile is complete."""
        try:
            profile = obj.profile
            return all([
                profile.nim,
                profile.full_name,
                profile.faculty,
                profile.major,
                profile.entry_year
            ])
        except StudentProfile.DoesNotExist:
            return False
    
    def get_memberships(self, obj):
        """Get user's active organization memberships."""
        from apps.organizations.models import OrganizationMember, MembershipStatus
        
        memberships = OrganizationMember.objects.filter(
            user=obj,
            status=MembershipStatus.ACTIVE
        ).select_related('organization').prefetch_related('roles')
        
        return MembershipSerializer(memberships, many=True).data

class AuthDataSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()

class RefreshTokenResponse(serializers.Serializer):
    data = AuthDataSerializer()

class LogoutResponse(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField(default="Logged out successfully")

class PasswordResetResponse(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()

class EmailPreferencesSerializer(serializers.Serializer):
    announcements = serializers.BooleanField(default=True)
    events = serializers.BooleanField(default=True)
    news = serializers.BooleanField(default=True)
    discussions = serializers.BooleanField(default=False)
    marketing = serializers.BooleanField(default=False)

    def update(self, instance, validated_data):
        # Update user.email_preferences JSONField or specific fields if model structure differs
        # Assuming user model has email_preferences JSONField for simplicity
        # or separate fields. Since we don't know the exact model structure for preferences,
        # we'll assume it returns the data for now or maps to fields.
        # This serializer is mainly for Documentation use here unless backed by model.
        # If it's used for Input/Output, we should ensure it matches User model fields.
        return super().update(instance, validated_data)
