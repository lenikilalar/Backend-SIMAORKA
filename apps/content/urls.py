from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnnouncementViewSet, NewsPostViewSet

router = DefaultRouter()
router.register(r'announcements', AnnouncementViewSet)
router.register(r'news', NewsPostViewSet)

urlpatterns = [
    path('orgs/<uuid:org_id>/content/', include(router.urls)), # Alternate access path if needed
    path('', include(router.urls)), # Default access
]
