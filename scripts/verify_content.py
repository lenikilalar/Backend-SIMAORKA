import os
import django
from django.conf import settings
from django.utils import timezone
import datetime

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
        print("No Org found.")
        return

    # 2. Create Announcement
    print("\nTesting Create Announcement...")
    payload = {
        'organization': org.id,
        'title': 'Internal Meeting',
        'content': 'Discussing proker.',
        'pinned': True
    }
    resp = c.post('/api/v1/announcements/', payload, content_type='application/json', **headers)
    if resp.status_code != 201:
        print("Create Announcement Failed:", resp.content)
    else:
        print("Create Announcement Success:", resp.json()['title'])

    # 3. Create News (Published)
    print("\nTesting Create News...")
    payload = {
        'organization': org.id,
        'title': 'Open Recruitment',
        'content': 'We are hiring.',
        'status': 'published'
    }
    resp = c.post('/api/v1/news/', payload, content_type='application/json', **headers)
    if resp.status_code != 201:
        print("Create News Failed:", resp.content)
    else:
        print("Create News Success:", resp.json()['title'])

    # 4. Create Event
    print("\nTesting Create Event...")
    start_at = timezone.now() + datetime.timedelta(days=1)
    end_at = start_at + datetime.timedelta(hours=2)
    payload = {
        'organization': org.id,
        'title': 'Grand Launching',
        'start_at': start_at.isoformat(),
        'end_at': end_at.isoformat(),
        'is_public': True
    }
    resp = c.post('/api/v1/events/', payload, content_type='application/json', **headers)
    if resp.status_code != 201:
        print("Create Event Failed:", resp.content)
    else:
        event_id = resp.json()['id']
        print("Create Event Success:", resp.json()['title'])

        # 5. RSVP Event
        print("Testing RSVP Event...")
        rsvp_url = f'/api/v1/events/{event_id}/attendance/'
        resp = c.post(rsvp_url, {'status': 'going'}, content_type='application/json', **headers)
        if resp.status_code != 200:
             print("RSVP Failed:", resp.content)
        else:
             print("RSVP Success:", resp.json())

if __name__ == '__main__':
    run_tests()
