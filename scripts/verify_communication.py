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
from apps.organizations.models import Organization

def run_tests():
    c = Client()
    
    # 1. Login
    print("Logging in...")
    resp = c.post('/api/v1/auth/google', {'id_token': 'testuser@example.com'}, content_type='application/json')
    token = resp.json()['access']
    headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'}
    
    org = Organization.objects.first()
    if not org:
        print("No organization found. Skipping tests.")
        return
    
    # 2. Create Discussion
    print("\nTesting Create Discussion...")
    payload = {
        'organization': org.id,
        'title': 'New Proker Idea',
    }
    resp = c.post('/api/v1/discussions/', payload, content_type='application/json', **headers) # type: ignore
    if resp.status_code != 201:
        print("Create Discussion Failed:", resp.content)
    else:
        thread_id = resp.json()['id']
        print("Create Discussion Success:", resp.json()['title'])

        # 3. Post Comment
        print("Testing Post Comment...")
        comment_url = f'/api/v1/discussions/{thread_id}/posts/'
        resp = c.post(comment_url, {'content': 'I agree!'}, content_type='application/json', **headers)
        if resp.status_code != 201:
             print("Post Failed:", resp.content)
        else:
             print("Post Success:", resp.json()['content'])

if __name__ == '__main__':
    run_tests()
