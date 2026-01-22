"""Web3 views for SIMAORKA API."""

from rest_framework import views, viewsets, permissions, status
from rest_framework.decorators import action
from django.utils import timezone
from django.conf import settings

from common.responses import success_response, error_response, created_response
from common.exceptions import ErrorCode
from common.permissions import IsSystemAdmin, IsOrgMemberActive

from .models import Web3Contract, UserWallet, OrgPeriod, OrgRoleCatalog, OrgRoleAssignment
from .serializers import (
    Web3ContractSerializer, UserWalletSerializer, WalletNonceSerializer, WalletVerifySerializer,
    OrgPeriodSerializer, OrgRoleCatalogSerializer, OrgRoleAssignmentSerializer,
    MintRoleNFTSerializer, RevokeRoleNFTSerializer
)
from . import services
from drf_spectacular.utils import extend_schema


@extend_schema(tags=['Web3'])
class Web3StatusView(views.APIView):
    """GET /api/v1/web3/status - Check if Web3 is enabled."""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        enabled = getattr(settings, 'WEB3_ENABLED', False)
        
        if not enabled:
            return success_response({
                'enabled': False,
                'message': 'Web3 features are not configured on this server.'
            })
        
        return success_response({
            'enabled': True,
            'chain': getattr(settings, 'WEB3_CHAIN', 'sepolia'),
            'chain_id': getattr(settings, 'WEB3_CHAIN_ID', 11155111),
            'contracts': {
                'role_nft': getattr(settings, 'ROLE_NFT_ADDRESS', ''),
                'gov_token': getattr(settings, 'GOV_TOKEN_ADDRESS', ''),
                'dues': getattr(settings, 'DUES_CONTRACT_ADDRESS', ''),
            }
        })


@extend_schema(tags=['Web3'])
class WalletNonceView(views.APIView):
    """POST /api/v1/web3/wallet/nonce - Get verification nonce for wallet."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = WalletNonceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        wallet_address = serializer.validated_data['wallet_address']
        chain = serializer.validated_data.get('chain', 'sepolia')
        
        wallet, message = services.create_wallet_verification(
            request.user, wallet_address, chain
        )
        
        return success_response({
            'wallet_address': wallet.wallet_address,
            'message': message,
            'nonce': wallet.verification_nonce
        })


@extend_schema(tags=['Web3'])
class WalletVerifyView(views.APIView):
    """POST /api/v1/web3/wallet/verify - Verify wallet ownership with signature."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = WalletVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        wallet_address = serializer.validated_data['wallet_address']
        signature = serializer.validated_data['signature']
        
        success, result = services.complete_wallet_verification(
            request.user, wallet_address, signature
        )
        
        if not success:
            return error_response(
                ErrorCode.WALLET_NOT_VERIFIED,
                result,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        return success_response(UserWalletSerializer(result).data)


@extend_schema(tags=['Web3'])
class UserWalletViewSet(viewsets.ReadOnlyModelViewSet):
    """User's verified wallets."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserWalletSerializer
    
    def get_queryset(self):
        return UserWallet.objects.filter(user=self.request.user)
    
    def list(self, request):
        wallets = self.get_queryset()
        return success_response(self.get_serializer(wallets, many=True).data)
    
    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        """Set a wallet as primary."""
        try:
            wallet = self.get_queryset().get(pk=pk, is_verified=True)
        except UserWallet.DoesNotExist:
            return error_response(ErrorCode.NOT_FOUND, "Wallet not found", status_code=status.HTTP_404_NOT_FOUND)
        
        # Unset other primary
        self.get_queryset().filter(is_primary=True).update(is_primary=False)
        wallet.is_primary = True
        wallet.save()
        
        return success_response(self.get_serializer(wallet).data)


@extend_schema(tags=['Web3'])
class ContractRegistryViewSet(viewsets.ReadOnlyModelViewSet):
    """View registered smart contracts."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = Web3ContractSerializer
    queryset = Web3Contract.objects.filter(is_active=True)
    
    def list(self, request):
        queryset = self.get_queryset()
        org_id = request.query_params.get('org_id')
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        return success_response(self.get_serializer(queryset, many=True).data)


@extend_schema(tags=['Web3'])
class RoleNFTViewSet(viewsets.ViewSet):
    """Role NFT management for organizations."""
    permission_classes = [permissions.IsAuthenticated, IsOrgMemberActive]
    
    def list(self, request, org_id=None):
        """List role NFT assignments for org."""
        assignments = OrgRoleAssignment.objects.filter(
            organization_id=org_id
        ).select_related('role', 'period')
        
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            assignments = assignments.filter(is_active=is_active.lower() == 'true')
        
        return success_response(OrgRoleAssignmentSerializer(assignments, many=True).data)
    
    @action(detail=False, methods=['post'])
    def record_mint(self, request, org_id=None):
        """Record a minted Role NFT (called after on-chain tx)."""
        serializer = MintRoleNFTSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        try:
            period = OrgPeriod.objects.get(id=data['period_id'], organization_id=org_id)
            role = OrgRoleCatalog.objects.get(organization_id=org_id, role_code=data['role_code'])
        except (OrgPeriod.DoesNotExist, OrgRoleCatalog.DoesNotExist):
            return error_response(ErrorCode.NOT_FOUND, "Period or role not found", status_code=status.HTTP_404_NOT_FOUND)
        
        from apps.organizations.models import Organization
        org = Organization.objects.get(id=org_id)
        
        # In real implementation, verify tx_hash on-chain before recording
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = None
        if data.get('user_id'):
            try:
                user = User.objects.get(id=data['user_id'])
            except User.DoesNotExist:
                pass
        
        assignment = services.record_role_nft_mint(
            organization=org,
            period=period,
            role=role,
            wallet_address=data['wallet_address'],
            token_id=request.data.get('token_id', 0),
            tx_hash=request.data.get('tx_hash', ''),
            user=user
        )
        
        return created_response(OrgRoleAssignmentSerializer(assignment).data)
    
    @action(detail=False, methods=['post'])
    def revoke(self, request, org_id=None):
        """Record a revoked Role NFT."""
        serializer = RevokeRoleNFTSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        assignment_id = serializer.validated_data['assignment_id']
        revoke_tx_hash = request.data.get('revoke_tx_hash', '')
        
        success, result = services.revoke_role_nft(assignment_id, revoke_tx_hash)
        
        if not success:
            return error_response(ErrorCode.NOT_FOUND, result, status_code=status.HTTP_404_NOT_FOUND)
        
        return success_response(OrgRoleAssignmentSerializer(result).data)


@extend_schema(tags=['Web3'])
class CheckRoleNFTView(views.APIView):
    """Check if wallet holds a valid Role NFT."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        wallet = request.query_params.get('wallet')
        org_id = request.query_params.get('org_id')
        role_code = request.query_params.get('role_code')
        
        if not all([wallet, org_id, role_code]):
            return error_response(ErrorCode.VALIDATION_ERROR, "Missing required params", status_code=status.HTTP_400_BAD_REQUEST)
        
        has_role = services.check_wallet_has_role_nft(wallet, org_id, role_code)
        
        return success_response({'has_role': has_role})
