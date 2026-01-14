from rest_framework import views, response, status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from .serializers import GoogleLoginSerializer, UserSerializer, RegisterSerializer, LoginSerializer
from .models import StudentProfile
import uuid

User = get_user_model()

class RegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        
        return response.Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = authenticate(email=email, password=password)
        
        if not user:
            return response.Response(
                {'error': 'Invalid credentials'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
             return response.Response(
                {'error': 'User account is disabled'}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        refresh = RefreshToken.for_user(user)
        
        return response.Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        })

class GoogleLoginView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = GoogleLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        id_token = serializer.validated_data['id_token']

        # TODO: Real Google Token Verification
        # For MVP/Development, we assume the token is valid or use a dummy check.
        # In production, use google.oauth2.id_token.verify_oauth2_token
        
        # MOCK IMPLEMENTATION:
        # We assume id_token is actually just the email for testing purposes 
        # OR we parse a dummy token structure. 
        # Let's assume for dev: `email:valid_token_string` or just `email` if simple.
        
        email = None
        if "@" in id_token:
             # Treat input as email for dev convenience if valid email format
             email = id_token
        else:
             # Fallback or real decode logic
             return response.Response({"error": "Invalid token (Dev: send email as token)"}, status=status.HTTP_400_BAD_REQUEST)

        # Get or Create User
        user, created = User.objects.get_or_create(email=email)
        if created:
            user.set_unusable_password()
            user.save()
            # Create empty profile placeholder
            StudentProfile.objects.create(
                user=user, 
                nim="", full_name="New User", faculty="", major="", entry_year=2024
            )

        refresh = RefreshToken.for_user(user)
        
        return response.Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        })

class UserMeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return response.Response(serializer.data)
