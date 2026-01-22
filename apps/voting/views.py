"""Voting views for SIMAORKA API."""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from django.utils import timezone

from common.responses import success_response, error_response
from common.exceptions import ErrorCode
from common.permissions import IsOrgMemberActive

from .models import Vote, VoteCast, VoteStatus
from .serializers import VoteSerializer, VoteCreateSerializer, VoteCastSerializer
from drf_spectacular.utils import extend_schema


@extend_schema(tags=['Voting'])
class VoteViewSet(viewsets.ModelViewSet):
    """ViewSet for organization voting sessions."""
    permission_classes = [permissions.IsAuthenticated, IsOrgMemberActive]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return VoteCreateSerializer
        return VoteSerializer
    
    def get_queryset(self):
        org_id = self.kwargs.get('org_id')
        return Vote.objects.filter(organization_id=org_id).prefetch_related('casts')
    
    def create(self, request, org_id=None):
        data = request.data.copy()
        data['organization'] = org_id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        vote = serializer.save(created_by=request.user)
        return success_response(VoteSerializer(vote).data, status_code=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def cast(self, request, pk=None, org_id=None):
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
