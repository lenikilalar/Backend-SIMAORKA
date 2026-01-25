"""
Documents URL routes.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet

router = DefaultRouter()
router.register('documents', DocumentViewSet, basename='documents')

# Nested under organization
urlpatterns = [
    path('orgs/<uuid:slug>/', include(router.urls)),
]
