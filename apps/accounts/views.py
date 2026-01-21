"""
Authentication views for SIMAORKA API following TSD V2.
"""

from rest_framework import views, permissions, status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model, authenticate
from django.conf import settings

from common.responses import success_response, error_response, created_response
from common.exceptions import ErrorCode

from .serializers import (
    GoogleLoginSerializer, UserSerializer, RegisterSerializer, 
    LoginSerializer, UserMeSerializer
)
from .models import StudentProfile

User = get_user_model()


class RegisterView(views.APIView):
    """POST /api/v1/auth/register - Register new user with email/password."""
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        
        return created_response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        })


class LoginView(views.APIView):
    """POST /api/v1/auth/login - Login with email/password."""
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = authenticate(email=email, password=password)
        
        if not user:
            return error_response(
                ErrorCode.INVALID_CREDENTIALS,
                "Invalid email or password.",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return error_response(
                ErrorCode.UNAUTHORIZED,
                "User account is disabled.",
                status_code=status.HTTP_403_FORBIDDEN
            )
            
        refresh = RefreshToken.for_user(user)
        
        response = success_response({
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        })
        
        # Set refresh token as HTTP-only cookie
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=60 * 60 * 24 * 7  # 7 days
        )
        
        return response


class GoogleLoginView(views.APIView):
    """POST /api/v1/auth/google - Login/register with Google OAuth token."""
    permission_classes = [permissions.AllowAny]
    serializer_class = GoogleLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        id_token = serializer.validated_data['id_token']

        # Verify Google token
        email = self._verify_google_token(id_token)
        
        if not email:
            return error_response(
                ErrorCode.INVALID_CREDENTIALS,
                "Invalid Google token.",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # Get or create user
        user, created = User.objects.get_or_create(email=email)
        if created:
            user.set_unusable_password()
            user.save()
            # Create empty profile placeholder
            StudentProfile.objects.create(
                user=user, 
                nim="", 
                full_name="", 
                faculty="", 
                major="", 
                entry_year=2024
            )

        refresh = RefreshToken.for_user(user)
        
        response = success_response({
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data,
            'is_new_user': created
        })
        
        # Set refresh token as HTTP-only cookie
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=60 * 60 * 24 * 7
        )
        
        return response
    
    def _verify_google_token(self, id_token):
        """
        Verify Google ID token and return email.
        In development, accepts email directly for testing.
        In production, uses google-auth library.
        """
        try:
            if settings.DEBUG:
                # Development mode: accept email directly for testing
                if "@" in id_token and "." in id_token.split("@")[-1]:
                    return id_token.lower()
                return None
            
            # Production: verify with Google
            from google.oauth2 import id_token as google_id_token
            from google.auth.transport import requests
            
            idinfo = google_id_token.verify_oauth2_token(
                id_token, 
                requests.Request(),
                getattr(settings, 'GOOGLE_CLIENT_ID', None)
            )
            
            return idinfo.get('email')
        except Exception:
            return None


class RefreshTokenView(views.APIView):
    """POST /api/v1/auth/refresh - Refresh access token using cookie."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            return error_response(
                ErrorCode.TOKEN_EXPIRED,
                "No refresh token found.",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            refresh = RefreshToken(refresh_token)
            return success_response({
                'access': str(refresh.access_token)
            })
        except TokenError:
            return error_response(
                ErrorCode.TOKEN_EXPIRED,
                "Refresh token expired or invalid.",
                status_code=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(views.APIView):
    """POST /api/v1/auth/logout - Logout and clear refresh cookie."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        response = success_response({'message': 'Logged out successfully.'})
        response.delete_cookie('refresh_token')
        return response


class UserMeView(views.APIView):
    """GET /api/v1/me - Get current user profile with memberships."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserMeSerializer(request.user, context={'request': request})
        return success_response(serializer.data)


class ForgotPasswordView(views.APIView):
    """POST /api/v1/auth/forgot-password - Request password reset email."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').lower().strip()
        
        if not email:
            return error_response(
                ErrorCode.VALIDATION_ERROR,
                "Email is required.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Always return success to prevent email enumeration
        try:
            user = User.objects.get(email=email)
            from common.email_service import send_password_reset_email
            send_password_reset_email(user)
        except User.DoesNotExist:
            pass  # Don't reveal if email exists
        
        return success_response({
            'message': 'If this email is registered, a reset link has been sent.'
        })


class ResetPasswordView(views.APIView):
    """POST /api/v1/auth/reset-password - Reset password with token."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get('token', '')
        password = request.data.get('password', '')
        
        if not token or not password:
            return error_response(
                ErrorCode.VALIDATION_ERROR,
                "Token and password are required.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if len(password) < 8:
            return error_response(
                ErrorCode.VALIDATION_ERROR,
                "Password must be at least 8 characters.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        from .models import PasswordResetToken
        from django.utils import timezone
        
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            
            if not reset_token.is_valid:
                return error_response(
                    ErrorCode.TOKEN_EXPIRED,
                    "Reset token has expired or already been used.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Reset password
            user = reset_token.user
            user.set_password(password)
            user.save()
            
            # Mark token as used
            reset_token.used_at = timezone.now()
            reset_token.save()
            
            return success_response({
                'message': 'Password has been reset successfully.'
            })
            
        except PasswordResetToken.DoesNotExist:
            return error_response(
                ErrorCode.NOT_FOUND,
                "Invalid reset token.",
                status_code=status.HTTP_400_BAD_REQUEST
            )


class EmailPreferencesView(views.APIView):
    """GET/PUT /api/v1/me/email-preferences - Manage email notification preferences."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .models import EmailPreference
        
        prefs, created = EmailPreference.objects.get_or_create(user=request.user)
        
        return success_response({
            'receive_announcements': prefs.receive_announcements,
            'receive_events': prefs.receive_events,
            'receive_finance': prefs.receive_finance,
            'receive_applications': prefs.receive_applications,
            'receive_system': prefs.receive_system,
            'digest_frequency': prefs.digest_frequency,
        })

    def put(self, request):
        from .models import EmailPreference, DigestFrequency
        
        prefs, created = EmailPreference.objects.get_or_create(user=request.user)
        
        # Update fields if provided
        if 'receive_announcements' in request.data:
            prefs.receive_announcements = bool(request.data['receive_announcements'])
        if 'receive_events' in request.data:
            prefs.receive_events = bool(request.data['receive_events'])
        if 'receive_finance' in request.data:
            prefs.receive_finance = bool(request.data['receive_finance'])
        if 'receive_applications' in request.data:
            prefs.receive_applications = bool(request.data['receive_applications'])
        if 'receive_system' in request.data:
            prefs.receive_system = bool(request.data['receive_system'])
        
        if 'digest_frequency' in request.data:
            freq = request.data['digest_frequency']
            if freq in [choice[0] for choice in DigestFrequency.choices]:
                prefs.digest_frequency = freq
        
        prefs.save()
        
        return success_response({
            'receive_announcements': prefs.receive_announcements,
            'receive_events': prefs.receive_events,
            'receive_finance': prefs.receive_finance,
            'receive_applications': prefs.receive_applications,
            'receive_system': prefs.receive_system,
            'digest_frequency': prefs.digest_frequency,
            'message': 'Preferences updated successfully.'
        })

