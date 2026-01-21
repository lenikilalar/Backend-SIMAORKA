"""Voting URL routes."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VoteViewSet

router = DefaultRouter()
router.register('votes', VoteViewSet, basename='votes')

urlpatterns = [path('orgs/<uuid:org_id>/', include(router.urls))]
