from django.urls import path
from .views import (
    GoogleLoginView, UserMeView, RegisterView, LoginView,
    RefreshTokenView, LogoutView
)

urlpatterns = [
    path('auth/register', RegisterView.as_view(), name='register'),
    path('auth/login', LoginView.as_view(), name='login'),
    path('auth/google', GoogleLoginView.as_view(), name='google_login'),
    path('auth/refresh', RefreshTokenView.as_view(), name='token_refresh'),
    path('auth/logout', LogoutView.as_view(), name='logout'),
    path('me', UserMeView.as_view(), name='user_me'),
]

