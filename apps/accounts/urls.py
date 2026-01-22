from django.urls import path
from .views import (
    GoogleLoginView, UserMeView, RegisterView, LoginView,
    RefreshTokenView, LogoutView, ForgotPasswordView, ResetPasswordView,
    EmailPreferencesView, UserMeProfileView
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/google/', GoogleLoginView.as_view(), name='google_login'),
    path('auth/refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('me/', UserMeView.as_view(), name='user_me'),
    path('me/profile/', UserMeProfileView.as_view(), name='user_profile'),
    path('me/email-preferences/', EmailPreferencesView.as_view(), name='email_preferences'),
]


