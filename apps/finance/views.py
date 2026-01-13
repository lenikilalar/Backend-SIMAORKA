from rest_framework import viewsets, permissions, status, decorators, response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import FinanceTransaction, FinanceLedger, Web3Payment, FinanceSource, FinanceTxType, FinanceVisibility
from .serializers import FinanceTransactionSerializer, FinanceLedgerSerializer, Web3SubmitSerializer, Web3PaymentSerializer
from apps.organizations.models import Organization
from decimal import Decimal

class FinanceTransactionViewSet(viewsets.ModelViewSet):
    queryset = FinanceTransaction.objects.all()
    serializer_class = FinanceTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filtering logic would go here (e.g. by org_id via query param)
        queryset = super().get_queryset()
        org_id = self.request.query_params.get('org_id')
        if org_id:
            queryset = queryset.filter(ledger__organization_id=org_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class Web3PaymentViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @decorators.action(detail=False, methods=['post'], url_path='submit')
    def submit_payment(self, request, org_id=None):
        """
        Endpoint: POST /api/v1/orgs/{org_id}/finance/web3/submit
        """
        org = get_object_or_404(Organization, id=org_id)
        serializer = Web3SubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 1. Find or create ledger for Web3
        ledger, _ = FinanceLedger.objects.get_or_create(
            organization=org, 
            name="Kas Web3",
            defaults={'currency': 'ETH'}
        )

        # 2. Create Transaction (Pending)
        # Convert Wei to Eth for storage (simplified)
        amount_eth = Decimal(data['amount_wei']) / Decimal(10**18)
        
        tx = FinanceTransaction.objects.create(
            ledger=ledger,
            type=FinanceTxType.INCOME,
            category="Dues",
            amount=amount_eth,
            description=data.get('note', 'Web3 Payment'),
            occurred_at=timezone.now(),
            created_by=request.user,
            source=FinanceSource.WEB3,
            visibility=FinanceVisibility.MEMBERS_ONLY
        )

        # 3. Create Web3 Payment Record
        web3_payment = Web3Payment.objects.create(
            transaction=tx,
            tx_hash=data['tx_hash'],
            wallet_address=data['wallet_address'],
            amount=amount_eth,
            chain=data.get('chain', 'other'),
            status='pending'
        )

        return response.Response({
            'id': web3_payment.id,
            'status': web3_payment.status,
            'tx_hash': web3_payment.tx_hash,
            'message': 'Payment recorded, waiting for verification.'
        }, status=status.HTTP_201_CREATED)

    @decorators.action(detail=False, methods=['get'], url_path='my-payments')
    def my_payments(self, request, org_id=None):
        """
        Endpoint: GET /api/v1/orgs/{org_id}/finance/web3/my-payments
        """
        payments = Web3Payment.objects.filter(
            transaction__created_by=request.user,
            transaction__ledger__organization_id=org_id
        )
        serializer = Web3PaymentSerializer(payments, many=True)
        return response.Response(serializer.data)

    @decorators.action(detail=True, methods=['post'], url_path='verify')
    def verify_payment(self, request, org_id=None, pk=None):
        """
        Endpoint: POST /api/v1/orgs/{org_id}/finance/web3/verify/{pk}
        Strictly for admins/treasurers. For Demo: auto-confirm.
        """
        # TODO: Check permissions (Treasurer/Admin)
        payment = get_object_or_404(Web3Payment, pk=pk)
        
        # MOCK VERIFICATION
        payment.status = 'confirmed'
        payment.confirmed_at = timezone.now()
        payment.save()

        return response.Response({
            'status': 'confirmed',
            'verified_at': payment.confirmed_at
        })
