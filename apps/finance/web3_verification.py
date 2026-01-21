"""
Web3 payment verification service for SIMAORKA.
Verifies blockchain transactions via RPC provider.
"""

import json
from decimal import Decimal
from django.conf import settings
from django.utils import timezone

# DuesPaid event signature: keccak256("DuesPaid(uint256,address,uint256,string)")
DUES_PAID_EVENT_SIGNATURE = "0x" + "DuesPaid(uint256,address,uint256,string)"


def get_web3_provider():
    """Get Web3 provider for RPC calls."""
    try:
        from web3 import Web3
        rpc_url = getattr(settings, 'SEPOLIA_RPC_URL', '')
        if not rpc_url:
            return None
        return Web3(Web3.HTTPProvider(rpc_url))
    except ImportError:
        return None


def get_dues_contract_address():
    """Get SimaorkaDues contract address from settings."""
    return getattr(settings, 'DUES_CONTRACT_ADDRESS', '')


def wei_to_eth(wei_value):
    """Convert wei to ETH."""
    return Decimal(wei_value) / Decimal(10**18)


def eth_to_wei(eth_value):
    """Convert ETH to wei."""
    return int(Decimal(eth_value) * Decimal(10**18))


def get_org_numeric_id(org_id):
    """
    Convert UUID org_id to numeric ID for smart contract.
    Uses a deterministic hash or stored numeric ID.
    """
    from apps.organizations.models import Organization
    try:
        org = Organization.objects.get(id=org_id)
        # If org has a numeric_id field, use it
        if hasattr(org, 'numeric_id') and org.numeric_id:
            return org.numeric_id
        # Otherwise, use hash of UUID (first 8 bytes as uint64)
        import hashlib
        hash_bytes = hashlib.sha256(str(org_id).encode()).digest()[:8]
        return int.from_bytes(hash_bytes, 'big')
    except Organization.DoesNotExist:
        return None


def verify_transaction(tx_hash, expected_contract=None, expected_org_id=None, expected_payer=None):
    """
    Verify a blockchain transaction.
    
    Checks:
    1. Transaction exists and succeeded (status=1)
    2. Transaction was sent to the correct contract
    3. DuesPaid event was emitted with correct data
    
    Returns:
        dict with keys: valid, data, error
    """
    w3 = get_web3_provider()
    if not w3:
        return {
            'valid': False,
            'data': None,
            'error': 'Web3 provider not configured (SEPOLIA_RPC_URL missing)'
        }
    
    contract_address = expected_contract or get_dues_contract_address()
    if not contract_address:
        return {
            'valid': False,
            'data': None,
            'error': 'Contract address not configured (DUES_CONTRACT_ADDRESS missing)'
        }
    
    try:
        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        
        if receipt is None:
            return {
                'valid': False,
                'data': None,
                'error': 'Transaction not found (may still be pending)'
            }
        
        # Check transaction status
        if receipt['status'] != 1:
            return {
                'valid': False,
                'data': {'receipt': dict(receipt)},
                'error': 'Transaction failed on-chain'
            }
        
        # Check contract address
        tx_to = receipt.get('to', '').lower()
        if tx_to != contract_address.lower():
            return {
                'valid': False,
                'data': {'to': tx_to, 'expected': contract_address},
                'error': f'Transaction sent to wrong contract: {tx_to}'
            }
        
        # Parse DuesPaid event from logs
        event_data = parse_dues_paid_event(receipt['logs'], w3)
        
        if not event_data:
            return {
                'valid': False,
                'data': {'logs': [dict(log) for log in receipt['logs']]},
                'error': 'DuesPaid event not found in transaction logs'
            }
        
        # Validate event data
        if expected_org_id is not None:
            if event_data['org_id'] != expected_org_id:
                return {
                    'valid': False,
                    'data': event_data,
                    'error': f"Org ID mismatch: expected {expected_org_id}, got {event_data['org_id']}"
                }
        
        if expected_payer:
            if event_data['payer'].lower() != expected_payer.lower():
                return {
                    'valid': False,
                    'data': event_data,
                    'error': f"Payer mismatch: expected {expected_payer}, got {event_data['payer']}"
                }
        
        # Success
        return {
            'valid': True,
            'data': {
                'tx_hash': tx_hash,
                'block_number': receipt['blockNumber'],
                'gas_used': receipt['gasUsed'],
                'org_id': event_data['org_id'],
                'payer': event_data['payer'],
                'amount_wei': str(event_data['amount_wei']),
                'amount_eth': str(wei_to_eth(event_data['amount_wei'])),
                'note': event_data.get('note', ''),
                'contract': contract_address
            },
            'error': None
        }
        
    except Exception as e:
        return {
            'valid': False,
            'data': None,
            'error': f'Verification error: {str(e)}'
        }


def parse_dues_paid_event(logs, w3):
    """
    Parse DuesPaid event from transaction logs.
    
    Event signature: DuesPaid(uint256 indexed orgId, address indexed payer, uint256 amountWei, string note)
    """
    # DuesPaid event topic (keccak256 hash)
    # keccak256("DuesPaid(uint256,address,uint256,string)")
    DUES_PAID_TOPIC = w3.keccak(text="DuesPaid(uint256,address,uint256,string)").hex()
    
    for log in logs:
        topics = log.get('topics', [])
        if not topics:
            continue
            
        # Check if this is a DuesPaid event
        event_topic = topics[0].hex() if hasattr(topics[0], 'hex') else topics[0]
        if event_topic.lower() != DUES_PAID_TOPIC.lower():
            continue
        
        # Parse indexed parameters from topics
        # topic[0] = event signature
        # topic[1] = orgId (indexed)
        # topic[2] = payer (indexed)
        if len(topics) < 3:
            continue
        
        org_id = int(topics[1].hex() if hasattr(topics[1], 'hex') else topics[1], 16)
        payer = '0x' + (topics[2].hex() if hasattr(topics[2], 'hex') else topics[2])[-40:]
        
        # Parse non-indexed parameters from data
        # data = amountWei (uint256) + note offset + note length + note data
        data = log.get('data', '0x')
        if isinstance(data, bytes):
            data = data.hex()
        if data.startswith('0x'):
            data = data[2:]
        
        if len(data) >= 64:
            amount_wei = int(data[:64], 16)
        else:
            amount_wei = 0
        
        # Note is encoded as dynamic string, simplified parsing
        note = ''
        if len(data) > 128:
            try:
                note_offset = int(data[64:128], 16) * 2
                note_length = int(data[128:192], 16)
                note_data = bytes.fromhex(data[192:192 + note_length * 2])
                note = note_data.decode('utf-8', errors='ignore')
            except Exception:
                pass
        
        return {
            'org_id': org_id,
            'payer': payer,
            'amount_wei': amount_wei,
            'note': note
        }
    
    return None


def verify_and_confirm_payment(payment_id):
    """
    Verify a pending Web3 payment and update its status.
    
    Args:
        payment_id: UUID of Web3Payment
    
    Returns:
        (success, payment, error_message)
    """
    from apps.finance.models import Web3Payment
    
    try:
        payment = Web3Payment.objects.get(id=payment_id)
    except Web3Payment.DoesNotExist:
        return False, None, "Payment not found"
    
    if payment.status != 'pending':
        return False, payment, f"Payment already {payment.status}"
    
    # Verify on blockchain
    result = verify_transaction(
        tx_hash=payment.tx_hash,
        expected_contract=payment.contract_address or None,
        expected_org_id=payment.org_numeric_id,
        expected_payer=payment.wallet_address
    )
    
    if result['valid']:
        payment.status = 'confirmed'
        payment.confirmed_at = timezone.now()
        payment.verification_data = result['data']
        payment.save()
        return True, payment, None
    else:
        payment.status = 'failed'
        payment.failure_reason = result['error']
        payment.verification_data = result.get('data')
        payment.save()
        return False, payment, result['error']


def check_wallet_balance(wallet_address):
    """Check wallet ETH balance (for debugging/display)."""
    w3 = get_web3_provider()
    if not w3:
        return None
    
    try:
        balance_wei = w3.eth.get_balance(wallet_address)
        return {
            'wei': str(balance_wei),
            'eth': str(wei_to_eth(balance_wei))
        }
    except Exception:
        return None
