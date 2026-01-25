"""Web3 URL routes."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    Web3StatusView, WalletNonceView, WalletVerifyView, UserWalletViewSet,
    ContractRegistryViewSet, RoleNFTViewSet, CheckRoleNFTView
)

router = DefaultRouter()
router.register('wallets', UserWalletViewSet, basename='wallets')
router.register('contracts', ContractRegistryViewSet, basename='contracts')

urlpatterns = [
    # Web3 status (public)
    path('web3/status', Web3StatusView.as_view(), name='web3_status'),
    
    # Wallet verification
    path('web3/wallet/nonce', WalletNonceView.as_view(), name='wallet_nonce'),
    path('web3/wallet/verify', WalletVerifyView.as_view(), name='wallet_verify'),
    path('web3/check-role', CheckRoleNFTView.as_view(), name='check_role_nft'),
    
    # User wallets
    path('web3/', include(router.urls)),
    
    # Org-scoped Role NFT management
    path('orgs/<uuid:slug>/role-nfts/', RoleNFTViewSet.as_view({'get': 'list'}), name='org_role_nfts'),
    path('orgs/<uuid:slug>/role-nfts/mint', RoleNFTViewSet.as_view({'post': 'record_mint'}), name='org_role_nft_mint'),
    path('orgs/<uuid:slug>/role-nfts/revoke', RoleNFTViewSet.as_view({'post': 'revoke'}), name='org_role_nft_revoke'),
]
