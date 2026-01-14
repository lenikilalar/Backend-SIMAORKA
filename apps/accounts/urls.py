from django.urls import path
from .views import GoogleLoginView, UserMeView, RegisterView, LoginView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('auth/register', RegisterView.as_view(), name='register'),
    path('auth/login', LoginView.as_view(), name='login'),
    path('auth/google', GoogleLoginView.as_view(), name='google_login'),
    path('auth/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('me', UserMeView.as_view(), name='user_me'),
]
