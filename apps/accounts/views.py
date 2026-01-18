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
