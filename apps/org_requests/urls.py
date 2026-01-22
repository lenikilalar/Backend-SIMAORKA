"""OrgRequests URL routes."""

from django.urls import path
from .views import PublicOrgRequestView, AdminOrgRequestViewSet

urlpatterns = [
    path('org-requests/', PublicOrgRequestView.as_view(), name='org_request_create'),
    path('admin/org-requests/', AdminOrgRequestViewSet.as_view({'get': 'list'}), name='admin_org_requests'),
    path('admin/org-requests/<uuid:pk>/', AdminOrgRequestViewSet.as_view({'get': 'retrieve'}), name='admin_org_request_detail'),
    path('admin/org-requests/<uuid:pk>/review/', AdminOrgRequestViewSet.as_view({'post': 'review'}), name='admin_org_request_review'),
]
