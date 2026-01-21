from rest_framework import serializers
from .models import FinanceTransaction, FinanceLedger, Web3Payment

class Web3PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Web3Payment
        fields = [
            'id', 'tx_hash', 'wallet_address', 'chain', 
            'amount', 'amount_wei', 'token_symbol', 
            'contract_address', 'org_numeric_id',
            'status', 'confirmed_at', 'failure_reason', 'created_at'
        ]
        read_only_fields = ('id', 'status', 'confirmed_at', 'failure_reason')

class FinanceTransactionSerializer(serializers.ModelSerializer):
    web3_payment = Web3PaymentSerializer(read_only=True)
    created_by_name = serializers.CharField(source='created_by.profile.full_name', read_only=True)
    ledger_name = serializers.CharField(source='ledger.name', read_only=True)

    class Meta:
        model = FinanceTransaction
        fields = ['id', 'ledger', 'ledger_name', 'type', 'category', 'amount', 'description', 'occurred_at', 
                  'visibility', 'source', 'web3_payment', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ('created_by', 'source')

class FinanceLedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinanceLedger
        fields = '__all__'

class Web3SubmitSerializer(serializers.Serializer):
    """Serializer for submitting Web3 payment proof."""
    tx_hash = serializers.CharField(max_length=66, help_text='Transaction hash from blockchain')
    wallet_address = serializers.CharField(max_length=42, help_text='Payer wallet address')
    amount_wei = serializers.CharField(max_length=78, help_text='Amount in Wei (string to avoid overflow)')
    chain = serializers.CharField(max_length=20, required=False, default='sepolia')
    contract_address = serializers.CharField(max_length=42, required=False, allow_blank=True, help_text='SimaorkaDues contract address')
    note = serializers.CharField(max_length=500, required=False, allow_blank=True, help_text='Payment note/description')

