import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    django.setup()
except Exception as e:
    print(f"Setup Error: {e}")
    exit(1)

from django.test import Client
import json

def run_tests():
    c = Client()

    # 1. Login
    print("Testing Login...")
    resp = c.post('/api/v1/auth/google', {'id_token': 'testuser@example.com'}, content_type='application/json')
    if resp.status_code != 200:
        print("Login Failed:", resp.content)
        return
    data = resp.json()
    print("Login Success. User:", data['user']['email'])
    token = data['access']

    # 2. Me
    print("\nTesting Me...")
    resp = c.get('/api/v1/me', HTTP_AUTHORIZATION=f'Bearer {token}')
    if resp.status_code != 200:
        print("Me Failed:", resp.content)
    else:
        print("Me Success:", resp.json()['email'])

    # 3. Create Org
    print("\nTesting Create Org...")
    org_data = {
        'name': 'BEM Kema',
        'description': 'Badan Eksekutif Mahasiswa'
    }
    resp = c.post('/api/v1/orgs/', org_data, content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {token}')
    if resp.status_code != 201:
        print("Create Org Failed:", resp.content)
        # Check permissions issues
        if resp.status_code == 403:
            print("Permission Denied (403)")
    else:
        print("Create Org Success:", resp.json()['slug'])

    # 4. List Orgs
    print("\nTesting List Orgs (Public)...")
    resp = c.get('/api/v1/public/organizations')
    if resp.status_code != 200:
        print("List Orgs Failed:", resp.content)
    else:
        data = resp.json()
        if 'results' in data:
            results = data['results']
        else:
            results = data # fallback
            
        print(f"List Orgs Success. Count: {len(results)}")
        if len(results) > 0:
            print("First Org:", results[0]['name'])

if __name__ == '__main__':
    run_tests()
