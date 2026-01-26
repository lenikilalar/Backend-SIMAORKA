from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, OrganizationMemberViewSet, OrganizationRequestViewSet, UserOrganizationsView

router = DefaultRouter()
router.register(r'orgs', OrganizationViewSet)
router.register(r'members', OrganizationMemberViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('public/organizations/', OrganizationViewSet.as_view({'get': 'public_list'}), name='public_orgs'),
    path('me/organizations/', UserOrganizationsView.as_view(), name='my_orgs'),
]

