from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, OrganizationMemberViewSet, OrganizationRequestViewSet

router = DefaultRouter()
router.register(r'orgs', OrganizationViewSet)
router.register(r'members', OrganizationMemberViewSet)
router.register(r'org-requests', OrganizationRequestViewSet) # For admin usage mostly

urlpatterns = [
    path('', include(router.urls)),
    path('public/organizations', OrganizationViewSet.as_view({'get': 'public_list'}), name='public_orgs'),
    path('public/org-requests', OrganizationRequestViewSet.as_view({'post': 'create'}), name='public_org_requests'),
]
