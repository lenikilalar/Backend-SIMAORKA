"""
Web3 Layer models for SIMAORKA.
Contracts, Wallets, Role NFT assignments.
"""

from django.db import models
from django.conf import settings
import uuid


class Web3Chain(models.TextChoices):
    ETHEREUM = 'ethereum', 'Ethereum'
    SEPOLIA = 'sepolia', 'Sepolia'
    POLYGON = 'polygon', 'Polygon'
    BSC = 'bsc', 'BSC'


class ContractType(models.TextChoices):
    ROLE_NFT = 'role_nft', 'Role NFT'
    GOV_TOKEN = 'gov_token', 'Governance Token'
    DUES = 'dues', 'Dues Contract'


class Web3Contract(models.Model):
    """Registry of deployed smart contracts."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    chain = models.CharField(max_length=20, choices=Web3Chain.choices, default=Web3Chain.SEPOLIA)
    contract_type = models.CharField(max_length=50, choices=ContractType.choices)
    address = models.CharField(max_length=42, unique=True)
    abi = models.JSONField(null=True, blank=True)
    
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, null=True, blank=True, related_name='contracts')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'web3_contracts'

    def __str__(self):
        return f"{self.contract_type} on {self.chain}: {self.address[:10]}..."


class UserWallet(models.Model):
    """User's verified Web3 wallets."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallets')
    
    wallet_address = models.CharField(max_length=42)
    chain = models.CharField(max_length=20, choices=Web3Chain.choices, default=Web3Chain.SEPOLIA)
    label = models.CharField(max_length=255, blank=True)
    
    # Verification
    verification_nonce = models.CharField(max_length=64, blank=True)
    verification_message = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_wallets'
        unique_together = ('user', 'wallet_address')

    def __str__(self):
        return f"{self.wallet_address[:10]}... ({self.user.email})"


class OrgPeriod(models.Model):
    """Organization period (kepengurusan)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='periods')
    
    name = models.CharField(max_length=255)  # e.g., "2024/2025"
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'org_periods'

    def __str__(self):
        return f"{self.organization.name} - {self.name}"


class OrgRoleCatalog(models.Model):
    """Catalog of roles that can be minted as NFTs."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='role_catalog')
    
    role_code = models.CharField(max_length=100)
    role_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'org_roles_catalog'
        unique_together = ('organization', 'role_code')

    def __str__(self):
        return f"{self.role_name} ({self.role_code})"


class OrgRoleAssignment(models.Model):
    """Record of minted Role NFT assignments."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='role_assignments')
    period = models.ForeignKey(OrgPeriod, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.ForeignKey(OrgRoleCatalog, on_delete=models.CASCADE, related_name='assignments')
    
    wallet_address = models.CharField(max_length=42)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='role_nft_assignments')
    
    token_id = models.PositiveBigIntegerField()
    tx_hash = models.CharField(max_length=66)
    
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoke_tx_hash = models.CharField(max_length=66, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'org_role_assignments'
        unique_together = ('organization', 'period', 'wallet_address', 'role')

    def __str__(self):
        return f"{self.role.role_name} -> {self.wallet_address[:10]}..."
