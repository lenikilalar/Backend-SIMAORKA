"""Voting serializers for SIMAORKA API."""

from rest_framework import serializers
from .models import Vote, VoteCast


class VoteCastSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoteCast
        fields = ['id', 'wallet_address', 'user', 'option_index', 'weight', 'cast_at']
        read_only_fields = ['id', 'weight', 'cast_at']


class VoteSerializer(serializers.ModelSerializer):
    results = serializers.SerializerMethodField()
    total_votes = serializers.SerializerMethodField()
    
    class Meta:
        model = Vote
        fields = [
            'id', 'organization', 'title', 'description', 'options',
            'type', 'status', 'start_at', 'end_at',
            'snapshot_block', 'gov_token_address',
            'results', 'total_votes', 'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']
    
    def get_results(self, obj):
        """Calculate voting results."""
        results = {}
        for i, option in enumerate(obj.options):
            if obj.type == 'token_weighted':
                total = sum(c.weight for c in obj.casts.filter(option_index=i))
            else:
                total = obj.casts.filter(option_index=i).count()
            results[option] = float(total)
        return results
    
    def get_total_votes(self, obj):
        return obj.casts.count()


class VoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ['organization', 'title', 'description', 'options', 'type', 'start_at', 'end_at', 'gov_token_address']
