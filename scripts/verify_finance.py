import os
import django
from django.conf import settings
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    django.setup()
except Exception as e:
    print(f"Setup Error: {e}")
    exit(1)

from django.test import Client
from apps.organizations.models import Organization
from apps.finance.models import FinanceTransaction

def run_tests():
    c = Client()
    
    # 1. Login (Reuse from previous)
    print("Logging in...")
    resp = c.post('/api/v1/auth/google', {'id_token': 'testuser@example.com'}, content_type='application/json')
    token = resp.json()['access']
    headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'}

    # 2. Get Org (Simulate)
    org = Organization.objects.first()
    if not org:
        print("No Org found to test finance.")
        return
    print(f"Using Org: {org.name} ({org.id})")

    # 3. Submit Web3 Payment
    print("\nTesting Web3 Submit...")
    payload = {
        'tx_hash': f'0xTestHash{uuid.uuid4().hex[:6]}',
        'wallet_address': '0xABC123',
        'amount_wei': '50000000000000000', # 0.05 ETH
        'note': 'Montly Dues'
    }
    url = f'/api/v1/orgs/{org.id}/finance/web3/submit'
    resp = c.post(url, payload, content_type='application/json', **headers)
    
    if resp.status_code != 201:
        print("Web3 Submit Failed:", resp.content)
    else:
        data = resp.json()
        print(f"Web3 Submit Success. ID: {data['id']}, Status: {data['status']}")
        payment_id = data['id']

        # 4. Verify Payment (Admin action)
        print("\nTesting Verify Payment...")
        verify_url = f'/api/v1/orgs/{org.id}/finance/web3/verify/{payment_id}'
        resp = c.post(verify_url, {}, **headers)
        if resp.status_code != 200:
             print("Verify Failed:", resp.content)
        else:
             print("Verify Success:", resp.json())

    # 5. List My Payments
    print("\nTesting My Payments...")
    list_url = f'/api/v1/orgs/{org.id}/finance/web3/my-payments'
    resp = c.get(list_url, **headers)
    results = resp.json()
    print(f"My Payments Count: {len(results)}")

if __name__ == '__main__':
    run_tests()
