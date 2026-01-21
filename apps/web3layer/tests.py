"""
Tests for Web3 layer.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from apps.web3layer.models import UserWallet, Web3Contract, Web3Chain
from apps.web3layer import services


User = get_user_model()


class WalletVerificationTests(TestCase):
    """Tests for wallet verification flow."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.wallet_address = '0x742d35Cc6634C0532925a3b844Bc9e7595f8fE28'
    
    def test_generate_nonce(self):
        """Test nonce generation."""
        nonce1 = services.generate_nonce()
        nonce2 = services.generate_nonce()
        
        self.assertEqual(len(nonce1), 64)  # 32 bytes hex = 64 chars
        self.assertNotEqual(nonce1, nonce2)  # Should be unique
    
    def test_get_verification_message(self):
        """Test verification message generation."""
        nonce = 'test_nonce_123'
        message = services.get_verification_message(self.wallet_address, nonce)
        
        self.assertIn(self.wallet_address, message)
        self.assertIn(nonce, message)
        self.assertIn('SIMAORKA', message)
    
    def test_create_wallet_verification(self):
        """Test creating wallet verification request."""
        wallet, message = services.create_wallet_verification(
            self.user, self.wallet_address
        )
        
        self.assertEqual(wallet.user, self.user)
        self.assertEqual(wallet.wallet_address, self.wallet_address.lower())
        self.assertFalse(wallet.is_verified)
        self.assertTrue(wallet.verification_nonce)
        self.assertIn(self.wallet_address.lower(), message)
    
    def test_create_wallet_updates_existing(self):
        """Test that creating verification for existing wallet updates it."""
        wallet1, _ = services.create_wallet_verification(self.user, self.wallet_address)
        nonce1 = wallet1.verification_nonce
        
        wallet2, _ = services.create_wallet_verification(self.user, self.wallet_address)
        nonce2 = wallet2.verification_nonce
        
        # Should be same wallet record with new nonce
        self.assertEqual(wallet1.id, wallet2.id)
        self.assertNotEqual(nonce1, nonce2)


class WalletModelTests(TestCase):
    """Tests for UserWallet model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='wallet@test.com',
            password='testpass'
        )
    
    def test_create_wallet(self):
        """Test creating a user wallet."""
        wallet = UserWallet.objects.create(
            user=self.user,
            wallet_address='0x1234567890123456789012345678901234567890',
            chain=Web3Chain.SEPOLIA
        )
        
        self.assertIsNotNone(wallet.id)
        self.assertEqual(wallet.chain, Web3Chain.SEPOLIA)
    
    def test_wallet_unique_per_user(self):
        """Test same address can't be added twice for same user."""
        address = '0x1234567890123456789012345678901234567890'
        
        UserWallet.objects.create(user=self.user, wallet_address=address)
        
        with self.assertRaises(Exception):
            UserWallet.objects.create(user=self.user, wallet_address=address)


class Web3ContractTests(TestCase):
    """Tests for Web3Contract model."""
    
    def test_create_contract(self):
        """Test creating a contract registry entry."""
        contract = Web3Contract.objects.create(
            chain=Web3Chain.SEPOLIA,
            contract_type='role_nft',
            address='0xAbCdEf0123456789012345678901234567890123'
        )
        
        self.assertTrue(contract.is_active)
        self.assertIn('role_nft', str(contract))


class RoleNFTServiceTests(TestCase):
    """Tests for Role NFT services."""
    
    def test_check_wallet_has_role_nft_empty(self):
        """Test checking role when no assignments exist."""
        has_role = services.check_wallet_has_role_nft(
            '0x1234',
            'fake-org-id',
            'ORG_ADMIN'
        )
        self.assertFalse(has_role)
