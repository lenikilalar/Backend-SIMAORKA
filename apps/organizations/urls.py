from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, OrganizationMemberViewSet

router = DefaultRouter()
router.register(r'orgs', OrganizationViewSet)
router.register(r'members', OrganizationMemberViewSet) # Might be better nested

urlpatterns = [
    path('', include(router.urls)),
    path('public/organizations', OrganizationViewSet.as_view({'get': 'list'}), name='public_orgs'),
]
