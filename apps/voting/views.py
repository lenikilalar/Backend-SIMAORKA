"""Voting views for SIMAORKA API."""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.request import Request
from typing import Any, cast
from django.utils import timezone

from common.responses import success_response, error_response
from common.exceptions import ErrorCode
from common.permissions import IsOrgMemberActive

from .models import Vote, VoteCast, VoteStatus
from .serializers import VoteSerializer, VoteCreateSerializer, VoteCastSerializer
from drf_spectacular.utils import extend_schema
from django.db.models import QuerySet


@extend_schema(tags=['Voting'])
class VoteViewSet(viewsets.ModelViewSet):
    """ViewSet for organization voting sessions."""
    permission_classes: Any = [permissions.IsAuthenticated, IsOrgMemberActive]
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    
    def get_serializer_class(self) -> type[VoteSerializer] | type[VoteCreateSerializer]:
        if self.action == 'create':
            return VoteCreateSerializer
        return VoteSerializer
    
    def get_queryset(self) -> QuerySet[Vote]:
        slug = self.kwargs.get('slug')
        return Vote.objects.filter(organization_id=slug).prefetch_related('casts')
    
    def create(self, request: Request, *args: Any, **kwargs: Any):
        slug = kwargs.get('slug')
        data = cast(dict[str, Any], request.data).copy()
        data['organization'] = slug
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        vote = serializer.save(created_by=request.user)
        return success_response(VoteSerializer(vote).data, status_code=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def cast(self, request, pk=None, slug=None):
        """Cast a vote on this voting session."""
        try:
            vote = self.get_queryset().get(pk=pk)
        except Vote.DoesNotExist:
            return error_response(ErrorCode.NOT_FOUND, "Vote not found", status_code=status.HTTP_404_NOT_FOUND)
        
        if vote.status != VoteStatus.ACTIVE:
            return error_response(ErrorCode.VOTE_CLOSED, "Voting is not active", status_code=status.HTTP_400_BAD_REQUEST)
        
        now = timezone.now()
        if now < vote.start_at or now > vote.end_at:
            return error_response(ErrorCode.VOTE_CLOSED, "Voting is not open", status_code=status.HTTP_400_BAD_REQUEST)
        
        option_index = request.data.get('option_index')
        wallet_address = request.data.get('wallet_address', '')
        
        if option_index is None or option_index >= len(vote.options):
            return error_response(ErrorCode.VALIDATION_ERROR, "Invalid option", status_code=status.HTTP_400_BAD_REQUEST)
        
        # Check existing vote
        if VoteCast.objects.filter(vote=vote, wallet_address=wallet_address).exists():
            return error_response(ErrorCode.VOTE_ALREADY_CAST, "Already voted", status_code=status.HTTP_400_BAD_REQUEST)
        
        cast = VoteCast.objects.create(
            vote=vote, user=request.user, wallet_address=wallet_address,
            option_index=option_index, weight=1
        )
        return success_response(VoteCastSerializer(cast).data, status_code=status.HTTP_201_CREATED)
