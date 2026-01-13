from rest_framework import serializers
from .models import FinanceTransaction, FinanceLedger, Web3Payment, UserWallet

class Web3PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Web3Payment
        fields = ['id', 'tx_hash', 'wallet_address', 'chain', 'amount', 'token_symbol', 'status', 'confirmed_at']
        read_only_fields = ('id', 'status', 'confirmed_at')

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
    tx_hash = serializers.CharField(max_length=255)
    wallet_address = serializers.CharField(max_length=255)
    amount_wei = serializers.CharField(max_length=255) # Keep as string to avoid overflow
    chain = serializers.CharField(max_length=50, required=False, default='sepolia')
    note = serializers.CharField(max_length=255, required=False)
