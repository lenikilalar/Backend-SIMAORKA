from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DiscussionViewSet, ChatViewSet

router = DefaultRouter()
router.register(r'discussions', DiscussionViewSet)
router.register(r'chats', ChatViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
