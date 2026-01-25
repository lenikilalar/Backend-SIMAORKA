"""Admin panel URL routes."""

from django.urls import path
from .views import AdminDashboardView, AdminOrgsViewSet, SetAdminView

urlpatterns = [
    path('admin/stats', AdminDashboardView.as_view(), name='admin_stats'),
    path('admin/orgs', AdminOrgsViewSet.as_view({'get': 'list'}), name='admin_orgs'),
    path('admin/orgs/<uuid:pk>', AdminOrgsViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'}), name='admin_org_detail'),
    path('admin/set-admin', SetAdminView.as_view(), name='set_admin'),
]
