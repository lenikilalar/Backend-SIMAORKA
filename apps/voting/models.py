"""
Voting models for SIMAORKA.
Supports hybrid token-weighted voting.
"""

from django.db import models
from django.conf import settings
import uuid


class VoteStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    ACTIVE = 'active', 'Active'
    CLOSED = 'closed', 'Closed'
    CANCELLED = 'cancelled', 'Cancelled'


class VoteType(models.TextChoices):
    SIMPLE = 'simple', 'Simple Majority'
    TOKEN_WEIGHTED = 'token_weighted', 'Token Weighted'


class Vote(models.Model):
    """Voting session."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='votes')
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    options = models.JSONField(default=list)  # List of option strings
    
    type = models.CharField(max_length=20, choices=VoteType.choices, default=VoteType.SIMPLE)
    status = models.CharField(max_length=20, choices=VoteStatus.choices, default=VoteStatus.DRAFT)
    
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    
    # For token-weighted votes
    snapshot_block = models.PositiveIntegerField(null=True, blank=True)
    gov_token_address = models.CharField(max_length=42, blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_votes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'votes'

    def __str__(self):
        return self.title


class VoteCast(models.Model):
    """Individual vote cast."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vote = models.ForeignKey(Vote, on_delete=models.CASCADE, related_name='casts')
    
    # For wallet-based voting
    wallet_address = models.CharField(max_length=42)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='vote_casts')
    
    option_index = models.PositiveIntegerField()  # Index in vote.options
    weight = models.DecimalField(max_digits=36, decimal_places=18, default=1)  # Token balance at snapshot
    
    cast_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vote_casts'
        unique_together = ('vote', 'wallet_address')  # One vote per wallet

    def __str__(self):
        return f"Vote on {self.vote.title} by {self.wallet_address}"
