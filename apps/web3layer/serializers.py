"""Web3 serializers for SIMAORKA API."""

from rest_framework import serializers
from .models import Web3Contract, UserWallet, OrgPeriod, OrgRoleCatalog, OrgRoleAssignment


class Web3ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Web3Contract
        fields = ['id', 'chain', 'contract_type', 'address', 'organization', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserWallet
        fields = ['id', 'wallet_address', 'chain', 'label', 'is_verified', 'is_primary', 'last_verified_at', 'created_at']
        read_only_fields = ['id', 'is_verified', 'last_verified_at', 'created_at']


class WalletNonceSerializer(serializers.Serializer):
    wallet_address = serializers.CharField(max_length=42)
    chain = serializers.ChoiceField(choices=['ethereum', 'sepolia', 'polygon', 'bsc'], default='sepolia')


class WalletVerifySerializer(serializers.Serializer):
    wallet_address = serializers.CharField(max_length=42)
    signature = serializers.CharField()


class OrgPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrgPeriod
        fields = ['id', 'name', 'start_date', 'end_date', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class OrgRoleCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrgRoleCatalog
        fields = ['id', 'role_code', 'role_name', 'description']


class OrgRoleAssignmentSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.role_name', read_only=True)
    period_name = serializers.CharField(source='period.name', read_only=True)
    
    class Meta:
        model = OrgRoleAssignment
        fields = [
            'id', 'organization', 'period', 'period_name', 'role', 'role_name',
            'wallet_address', 'user', 'token_id', 'tx_hash',
            'is_active', 'revoked_at', 'revoke_tx_hash', 'expires_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class MintRoleNFTSerializer(serializers.Serializer):
    period_id = serializers.UUIDField()
    role_code = serializers.CharField(max_length=100)
    wallet_address = serializers.CharField(max_length=42)
    user_id = serializers.UUIDField(required=False)


class RevokeRoleNFTSerializer(serializers.Serializer):
    assignment_id = serializers.UUIDField()
