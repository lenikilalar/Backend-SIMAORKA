from django.db import models
from django.conf import settings
import uuid

class FinanceTxType(models.TextChoices):
    INCOME = 'income', 'Income'
    EXPENSE = 'expense', 'Expense'

class FinanceVisibility(models.TextChoices):
    MEMBERS_ONLY = 'members_only', 'Members Only'
    PUBLIC_SUMMARY = 'public_summary', 'Public Summary'

class FinanceSource(models.TextChoices):
    MANUAL = 'manual', 'Manual'
    WEB3 = 'web3', 'Web3'

class Web3Chain(models.TextChoices):
    ETHEREUM = 'ethereum', 'Ethereum'
    POLYGON = 'polygon', 'Polygon'
    BSC = 'bsc', 'BSC'
    OTHER = 'other', 'Other'

class Web3PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    FAILED = 'failed', 'Failed'

class FinanceLedger(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='ledgers')
    name = models.CharField(max_length=255)
    currency = models.CharField(max_length=10, default='IDR')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'finance_ledgers'
        unique_together = ('organization', 'name')

    def __str__(self):
        return f"{self.name} ({self.organization})"

class FinanceTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ledger = models.ForeignKey(FinanceLedger, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=20, choices=FinanceTxType.choices)
    category = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    description = models.TextField(null=True, blank=True)
    occurred_at = models.DateTimeField()
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_transactions')
    attachment_url = models.TextField(null=True, blank=True)
    visibility = models.CharField(max_length=20, choices=FinanceVisibility.choices, default=FinanceVisibility.MEMBERS_ONLY)
    source = models.CharField(max_length=20, choices=FinanceSource.choices, default=FinanceSource.MANUAL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'finance_transactions'

class Web3Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.OneToOneField(FinanceTransaction, on_delete=models.CASCADE, related_name='web3_payment')
    wallet_address = models.CharField(max_length=255)
    chain = models.CharField(max_length=20, choices=Web3Chain.choices, default=Web3Chain.OTHER)
    tx_hash = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    token_symbol = models.CharField(max_length=20, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=Web3PaymentStatus.choices, default=Web3PaymentStatus.PENDING)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'web3_payments'
