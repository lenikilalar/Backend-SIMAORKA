"""Web3 services for wallet verification and NFT operations."""

import secrets
import hashlib
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

from eth_account.messages import encode_defunct
from web3 import Web3

from .models import UserWallet, OrgRoleAssignment, OrgRoleCatalog, OrgPeriod


def generate_nonce():
    """Generate a random nonce for wallet verification."""
    return secrets.token_hex(32)


def get_verification_message(wallet_address, nonce):
    """Generate the message to be signed for wallet verification."""
    return f"""SIMAORKA Wallet Verification

Please sign this message to verify ownership of your wallet.

Wallet: {wallet_address}
Nonce: {nonce}
Timestamp: {timezone.now().isoformat()}

This signature will not cost any gas fees."""


def create_wallet_verification(user, wallet_address, chain='sepolia'):
    """Create or update wallet with new verification nonce."""
    nonce = generate_nonce()
    message = get_verification_message(wallet_address, nonce)
    
    wallet, created = UserWallet.objects.update_or_create(
        user=user,
        wallet_address=wallet_address.lower(),
        defaults={
            'chain': chain,
            'verification_nonce': nonce,
            'verification_message': message,
            'is_verified': False
        }
    )
    
    return wallet, message


def verify_wallet_signature(wallet_address, signature, message):
    """
    Verify an Ethereum signature.
    Returns True if the signature is valid for the given message and address.
    """
    try:
        w3 = Web3()
        message_hash = encode_defunct(text=message)
        recovered_address = w3.eth.account.recover_message(message_hash, signature=signature)
        return recovered_address.lower() == wallet_address.lower()
    except Exception:
        return False


def complete_wallet_verification(user, wallet_address, signature):
    """
    Complete wallet verification by validating the signature.
    Returns (success, wallet_or_error_message)
    """
    try:
        wallet = UserWallet.objects.get(user=user, wallet_address=wallet_address.lower())
    except UserWallet.DoesNotExist:
        return False, "Wallet not found. Please request a nonce first."
    
    if not wallet.verification_message:
        return False, "No pending verification. Please request a new nonce."
    
    # Verify signature
    if not verify_wallet_signature(wallet_address, signature, wallet.verification_message):
        return False, "Invalid signature."
    
    # Mark as verified
    wallet.is_verified = True
    wallet.last_verified_at = timezone.now()
    wallet.verification_nonce = ''  # Clear nonce after use
    wallet.save()
    
    # Set as primary if no other primary exists
    if not UserWallet.objects.filter(user=user, is_primary=True).exists():
        wallet.is_primary = True
        wallet.save()
    
    return True, wallet


def get_web3_provider():
    """Get Web3 provider for RPC calls."""
    rpc_url = getattr(settings, 'SEPOLIA_RPC_URL', '')
    if not rpc_url:
        return None
    return Web3(Web3.HTTPProvider(rpc_url))


def record_role_nft_mint(organization, period, role, wallet_address, token_id, tx_hash, user=None, expires_at=None):
    """
    Record a minted Role NFT assignment.
    Called after successful on-chain minting.
    """
    assignment = OrgRoleAssignment.objects.create(
        organization=organization,
        period=period,
        role=role,
        wallet_address=wallet_address.lower(),
        user=user,
        token_id=token_id,
        tx_hash=tx_hash,
        is_active=True,
        expires_at=expires_at or (timezone.now() + timedelta(days=365))
    )
    return assignment


def revoke_role_nft(assignment_id, revoke_tx_hash):
    """
    Mark a Role NFT as revoked.
    Called after successful on-chain revocation.
    """
    try:
        assignment = OrgRoleAssignment.objects.get(id=assignment_id, is_active=True)
        assignment.is_active = False
        assignment.revoked_at = timezone.now()
        assignment.revoke_tx_hash = revoke_tx_hash
        assignment.save()
        return True, assignment
    except OrgRoleAssignment.DoesNotExist:
        return False, "Assignment not found or already revoked."


def check_wallet_has_role_nft(wallet_address, organization_id, role_code):
    """Check if a wallet holds an active Role NFT for the given role."""
    return OrgRoleAssignment.objects.filter(
        wallet_address=wallet_address.lower(),
        organization_id=organization_id,
        role__role_code=role_code,
        is_active=True,
        expires_at__gt=timezone.now()
    ).exists()
