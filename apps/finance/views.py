from rest_framework import viewsets, permissions, status, decorators, response, serializers
from typing import cast, Any
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import FinanceTransaction, FinanceLedger, Web3Payment, FinanceSource, FinanceTxType, FinanceVisibility
from .serializers import FinanceTransactionSerializer, FinanceLedgerSerializer, Web3SubmitSerializer, Web3PaymentSerializer
from apps.organizations.models import Organization
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.request import Request
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from datetime import timedelta
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiParameter
from typing import Any
from common.permissions import IsOrgMemberActive
from common.responses import error_response
from common.exceptions import ErrorCode


@extend_schema(tags=['Finance'])
class FinanceTransactionViewSet(viewsets.ModelViewSet):
    queryset = FinanceTransaction.objects.all()
    serializer_class = FinanceTransactionSerializer
    permission_classes: Any = [permissions.IsAuthenticated, IsOrgMemberActive]

    def get_queryset(self):
        # Filtering logic would go here (e.g. by org_id via query param)
        queryset = super().get_queryset()
        request = cast(Request, self.request)
        org_id = request.query_params.get('org_id')
        if org_id:
            queryset = queryset.filter(ledger__organization_id=org_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

@extend_schema(tags=['Web3'])
class Web3PaymentViewSet(viewsets.ViewSet):
    """Handle Web3 payments and verification."""
    permission_classes: Any = [permissions.IsAuthenticated]

    @decorators.action(detail=False, methods=['post'], url_path='submit')
    def submit_payment(self, request, slug=None):
        org = get_object_or_404(Organization, id=slug)
        serializer = Web3SubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)
        
        # Check if tx_hash already exists (duplicate submission)
        existing = Web3Payment.objects.filter(tx_hash=data['tx_hash']).first()
        if existing:
            return response.Response({
                'id': existing.id,
                'status': existing.status,
                'tx_hash': existing.tx_hash,
                'message': 'Payment already recorded.'
            }, status=status.HTTP_200_OK)

        # Get or create ETH ledger for this org
        ledger, _ = FinanceLedger.objects.get_or_create(
            organization=org, 
            name="Kas Web3",
            defaults={'currency': 'ETH'}
        )

        # Convert Wei to ETH
        amount_wei = data['amount_wei']
        amount_eth = Decimal(amount_wei) / Decimal(10**18)
        
        # Get org numeric ID for contract verification
        from .web3_verification import get_org_numeric_id, get_dues_contract_address
        org_numeric_id = get_org_numeric_id(slug)
        contract_address = data.get('contract_address', '') or get_dues_contract_address()
        
        # Create finance transaction
        tx = FinanceTransaction.objects.create(
            ledger=ledger,
            type=FinanceTxType.INCOME,
            category="Iuran Web3",
            amount=amount_eth,
            description=data.get('note', 'Pembayaran kas via Web3'),
            occurred_at=timezone.now(),
            created_by=request.user,
            source=FinanceSource.WEB3,
            visibility=FinanceVisibility.MEMBERS_ONLY
        )

        # Create Web3 payment record
        web3_payment = Web3Payment.objects.create(
            transaction=tx,
            tx_hash=data['tx_hash'],
            wallet_address=data['wallet_address'].lower(),
            amount=amount_eth,
            amount_wei=str(amount_wei),
            chain=data.get('chain', 'sepolia'),
            contract_address=contract_address,
            org_numeric_id=org_numeric_id,
            token_symbol='ETH',
            status='pending'
        )

        return response.Response({
            'id': str(web3_payment.id),
            'status': web3_payment.status,
            'tx_hash': web3_payment.tx_hash,
            'amount_eth': str(amount_eth),
            'message': 'Pembayaran dicatat, menunggu verifikasi blockchain.'
        }, status=status.HTTP_201_CREATED)

    @decorators.action(detail=False, methods=['get'], url_path='my-payments')
    def my_payments(self, request, slug=None):
        """
        Endpoint: GET /api/v1/orgs/{org_id}/finance/web3/my-payments
        """
        payments = Web3Payment.objects.filter(
            transaction__created_by=request.user,
            transaction__ledger__organization_id=slug
        )
        serializer = Web3PaymentSerializer(payments, many=True)
        return response.Response(serializer.data)

    @decorators.action(detail=True, methods=['post'], url_path='verify')
    def verify_payment(self, request, slug=None, pk=None):
        """
        Endpoint: POST /api/v1/orgs/{org_id}/finance/web3/verify/{pk}
        
        Verify a pending Web3 payment by checking the blockchain.
        Access: Treasurer / Admin Organisasi
        """
        # TODO: Check permissions (Treasurer/Admin)
        payment = get_object_or_404(Web3Payment, pk=pk)
        
        if payment.status == 'confirmed':
            return response.Response({
                'status': 'confirmed',
                'verified_at': payment.confirmed_at,
                'message': 'Payment already verified.'
            })
        
        # Use manual verification mode if requested
        if request.data.get('manual', False):
            payment.status = 'confirmed'
            payment.confirmed_at = timezone.now()
            payment.verification_data = {'mode': 'manual', 'verified_by': str(request.user.id)}
            payment.save()
            return response.Response({
                'status': 'confirmed',
                'verified_at': payment.confirmed_at,
                'mode': 'manual'
            })
        
        # Blockchain verification
        from .web3_verification import verify_and_confirm_payment
        success, updated_payment, error = verify_and_confirm_payment(pk)
        
        if success and updated_payment:
            return response.Response({
                'status': 'confirmed',
                'verified_at': updated_payment.confirmed_at,
                'verification_data': updated_payment.verification_data
            })
        else:
            return response.Response({
                'status': updated_payment.status if updated_payment else 'error',
                'error': error,
                'message': 'Verifikasi blockchain gagal. Gunakan {"manual": true} untuk verifikasi manual.'
            }, status=status.HTTP_400_BAD_REQUEST)

    @decorators.action(detail=False, methods=['get'], url_path='payments')
    def all_payments(self, request, slug=None):
        """
        Endpoint: GET /api/v1/orgs/{org_id}/finance/web3/payments
        List all Web3 payments for an organization.
        Access: Treasurer / Admin Organisasi / Superadmin
        """
        # TODO: Check permissions (Treasurer/Admin)
        payments = Web3Payment.objects.filter(
            transaction__ledger__organization_id=slug
        ).select_related('transaction', 'transaction__created_by').order_by('-created_at')
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter in ['pending', 'confirmed', 'failed']:
            payments = payments.filter(status=status_filter)
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
        offset = (page - 1) * limit
        
        total = payments.count()
        payments_page = payments[offset:offset + limit]
        
        data = []
        for p in payments_page:
            data.append({
                'id': str(p.id),
                'tx_hash': p.tx_hash,
                'wallet_address': p.wallet_address,
                'amount': float(p.amount),
                'chain': p.chain,
                'status': p.status,
                'confirmed_at': p.confirmed_at.isoformat() if p.confirmed_at else None,
                'created_at': p.created_at.isoformat(),
                'user': {
                    'id': str(p.transaction.created_by.id) if p.transaction.created_by else None,
                    'email': p.transaction.created_by.email if p.transaction.created_by else None,
                    'full_name': getattr(p.transaction.created_by, 'full_name', '') if p.transaction.created_by else None
                },
                'note': p.transaction.description
            })
        
        return response.Response({
            'data': data,
            'meta': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': (total + limit - 1) // limit
            }
        })



@extend_schema(tags=['Finance'])
class FinanceSummaryView(APIView):
    """Get finance summary for an organization."""
    permission_classes: Any = [permissions.IsAuthenticated]
    
    def get(self, request: Request, slug=None):
        org = get_object_or_404(Organization, id=slug)
        
        # Get all transactions for this org
        transactions = FinanceTransaction.objects.filter(
            ledger__organization=org
        )
        
        # Calculate totals
        total_income = transactions.filter(
            type=FinanceTxType.INCOME
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        total_expense = transactions.filter(
            type=FinanceTxType.EXPENSE
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        balance = total_income - total_expense
        
        # Transaction counts
        tx_count = transactions.count()
        income_count = transactions.filter(type=FinanceTxType.INCOME).count()
        expense_count = transactions.filter(type=FinanceTxType.EXPENSE).count()
        
        # Web3 stats
        web3_payments = Web3Payment.objects.filter(
            transaction__ledger__organization=org
        )
        web3_total = web3_payments.filter(
            status='confirmed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        web3_pending_count = web3_payments.filter(status='pending').count()
        
        # Recent transactions (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_income = transactions.filter(
            type=FinanceTxType.INCOME,
            occurred_at__gte=thirty_days_ago
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        recent_expense = transactions.filter(
            type=FinanceTxType.EXPENSE,
            occurred_at__gte=thirty_days_ago
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Category breakdown (top 5 expense categories)
        expense_by_category = transactions.filter(
            type=FinanceTxType.EXPENSE
        ).values('category').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')[:5]
        
        income_by_category = transactions.filter(
            type=FinanceTxType.INCOME
        ).values('category').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')[:5]
        
        # Monthly trend (last 6 months)
        six_months_ago = timezone.now() - timedelta(days=180)
        monthly_data = transactions.filter(
            occurred_at__gte=six_months_ago
        ).annotate(
            month=TruncMonth('occurred_at')
        ).values('month', 'type').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        # Format monthly trend
        monthly_trend = {}
        for item in monthly_data:
            month_key = item['month'].strftime('%Y-%m') if item['month'] else 'unknown'
            if month_key not in monthly_trend:
                monthly_trend[month_key] = {'income': 0, 'expense': 0}
            monthly_trend[month_key][item['type']] = float(item['total'])
        
        # Ledgers summary
        ledgers = FinanceLedger.objects.filter(organization=org)
        ledger_summaries = []
        for ledger in ledgers:
            ledger_txs = transactions.filter(ledger=ledger)
            ledger_income = ledger_txs.filter(
                type=FinanceTxType.INCOME
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            ledger_expense = ledger_txs.filter(
                type=FinanceTxType.EXPENSE
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            ledger_summaries.append({
                'id': str(ledger.id),
                'name': ledger.name,
                'currency': ledger.currency,
                'income': float(ledger_income),
                'expense': float(ledger_expense),
                'balance': float(ledger_income - ledger_expense),
                'transaction_count': ledger_txs.count()
            })
        
        return response.Response({
            'data': {
                'organization_id': str(org.id),
                'organization_name': org.name,
                
                # Overall totals
                'totals': {
                    'income': float(total_income),
                    'expense': float(total_expense),
                    'balance': float(balance),
                    'transaction_count': tx_count,
                    'income_count': income_count,
                    'expense_count': expense_count
                },
                
                # Last 30 days
                'recent': {
                    'income': float(recent_income),
                    'expense': float(recent_expense),
                    'net': float(recent_income - recent_expense),
                    'period_days': 30
                },
                
                # Web3 payments
                'web3': {
                    'total_confirmed': float(web3_total),
                    'pending_count': web3_pending_count,
                    'currency': 'ETH'
                },
                
                # Category breakdowns
                'categories': {
                    'income': [
                        {
                            'category': item['category'] or 'Uncategorized',
                            'total': float(item['total']),
                            'count': item['count']
                        }
                        for item in income_by_category
                    ],
                    'expense': [
                        {
                            'category': item['category'] or 'Uncategorized',
                            'total': float(item['total']),
                            'count': item['count']
                        }
                        for item in expense_by_category
                    ]
                },
                
                # Monthly trend
                'monthly_trend': [
                    {
                        'month': month,
                        'income': data['income'],
                        'expense': data['expense'],
                        'net': data['income'] - data['expense']
                    }
                    for month, data in sorted(monthly_trend.items())
                ],
                
                # Ledger breakdown
                'ledgers': ledger_summaries,
                
                # Metadata
                'generated_at': timezone.now().isoformat()
            }
        })


class PublicFinanceView(APIView):
    """Public view for organization finance transparency."""
    permission_classes: Any = [permissions.AllowAny]
    
    @extend_schema(
        summary="Get public finance summary",
        description="Returns financial summary for organizations with transparency enabled. No auth required.",
        responses={
            200: inline_serializer(
                name='PublicFinanceResponse',
                fields={
                    'organization': serializers.CharField(),
                    'transparency_level': serializers.CharField(),
                    'note': serializers.CharField(),
                    'totals': serializers.DictField(),
                    'categories': serializers.DictField(),
                    'last_updated': serializers.DateTimeField(),
                }
            ),
            403: inline_serializer(
                name='FinancePrivateError',
                fields={'error': serializers.DictField()}
            )
        },
        tags=['Public Finance']
    )
    def get(self, request: Request, slug=None):
        org = get_object_or_404(Organization, id=slug)
        
        # Verify transparency settings
        if org.finance_transparency == 'private':
            return error_response(ErrorCode.PERMISSION_DENIED, "Finance transparency disabled", status_code=status.HTTP_403_FORBIDDEN)
        
        # Get transactions
        transactions = FinanceTransaction.objects.filter(
            ledger__organization=org
        )
        
        # Calculate totals
        income_result = transactions.filter(
            type=FinanceTxType.INCOME
        ).aggregate(total=Sum('amount'))
        total_income = income_result['total'] or Decimal('0')
        
        expense_result = transactions.filter(
            type=FinanceTxType.EXPENSE
        ).aggregate(total=Sum('amount'))
        total_expense = expense_result['total'] or Decimal('0')
        
        balance = total_income - total_expense
        
        # Category breakdown
        income_by_category = transactions.filter(
            type=FinanceTxType.INCOME
        ).values('category').annotate(
            total=Sum('amount')
        ).order_by('-total')[:10]
        
        expense_by_category = transactions.filter(
            type=FinanceTxType.EXPENSE
        ).values('category').annotate(
            total=Sum('amount')
        ).order_by('-total')[:10]
        
        data = {
            'organization': org.name,
            'transparency_level': org.finance_transparency,
            'note': org.finance_transparency_note,
            
            'totals': {
                'income': float(total_income),
                'expense': float(total_expense),
                'balance': float(balance)
            },
            
            'categories': {
                'income': [
                    {'category': item['category'] or 'Lainnya', 'total': float(item['total'])}
                    for item in income_by_category
                ],
                'expense': [
                    {'category': item['category'] or 'Lainnya', 'total': float(item['total'])}
                    for item in expense_by_category
                ]
            },
            
            'last_updated': timezone.now().isoformat()
        }
        
        return response.Response({'data': data})


class PublicFinanceTransactionsView(APIView):
    """
    GET /api/v1/organizations/{slug}/finance/public/transactions
    
    Public transaction list (only if full transparency).
    Names and wallets are anonymized.
    """
    permission_classes: Any = [permissions.AllowAny]
    
    @extend_schema(
        summary="Get public transactions list",
        description="Returns transaction list for organizations with full transparency. No auth required.",
        parameters=[
            OpenApiParameter(name='page', location=OpenApiParameter.QUERY, type=int, description='Page number'),
            OpenApiParameter(name='limit', location=OpenApiParameter.QUERY, type=int, description='Items per page'),
        ],
        responses={
            200: inline_serializer(
                name='PublicTransactionsResponse',
                fields={
                    'data': serializers.ListField(),
                    'meta': serializers.DictField(),
                }
            ),
            403: inline_serializer(
                name='TransparencyError',
                fields={'error': serializers.DictField()}
            )
        },
        tags=['Public Finance']
    )
    def get(self, request: Request, slug=None):
        org = get_object_or_404(Organization, slug=slug)
        
        # Only allow for full transparency
        if org.finance_transparency != 'full':
            return response.Response({
                'error': {
                    'code': 'TRANSPARENCY_LEVEL_INSUFFICIENT',
                    'message': 'Daftar transaksi hanya tersedia untuk organisasi dengan transparansi penuh.'
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        transactions = FinanceTransaction.objects.filter(
            ledger__organization=org
        ).order_by('-occurred_at')
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
        offset = (page - 1) * limit
        
        total = transactions.count()
        transactions_page = transactions[offset:offset + limit]
        
        data = []
        for tx in transactions_page:
            data.append({
                'date': tx.occurred_at.strftime('%Y-%m-%d'),
                'type': tx.type,
                'category': tx.category or 'Lainnya',
                'amount': float(tx.amount),
                'description': tx.description[:100] if tx.description else None  # Truncate
            })
        
        return response.Response({
            'data': data,
            'meta': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': (total + limit - 1) // limit
            }
        })


