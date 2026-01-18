"""
Common utility functions for SIMAORKA API.
"""

import hashlib
from django.utils import timezone


def hash_file(file):
    """
    Calculate SHA256 hash of a file.
    Used for document version integrity.
    """
    sha256 = hashlib.sha256()
    for chunk in file.chunks():
        sha256.update(chunk)
    return sha256.hexdigest()


def is_within_window(start_at, end_at, now=None):
    """
    Check if current time is within a time window.
    Used for open_member window validation.
    """
    if now is None:
        now = timezone.now()
    
    if start_at and now < start_at:
        return False
    if end_at and now > end_at:
        return False
    return True


def generate_nonce():
    """
    Generate a random nonce for Web3 wallet verification.
    """
    import secrets
    return secrets.token_hex(16)


def keccak256(text):
    """
    Calculate keccak256 hash (for Web3 role code matching).
    """
    from eth_utils import keccak
    if isinstance(text, str):
        text = text.encode('utf-8')
    return keccak(text).hex()


def wei_to_eth(wei):
    """Convert Wei to ETH."""
    from decimal import Decimal
    return Decimal(wei) / Decimal(10**18)


def eth_to_wei(eth):
    """Convert ETH to Wei."""
    from decimal import Decimal
    return int(Decimal(eth) * Decimal(10**18))
