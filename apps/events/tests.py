from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime
from apps.organizations.models import Organization

User = get_user_model()

class EventTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='eventuser', email='event@test.com', password='password')
        self.client.force_authenticate(user=self.user)
        self.org = Organization.objects.create(name='Event Org', description='Desc', slug='event-org')

    def test_event_lifecycle(self):
        # 1. Create Event
        start_at = timezone.now() + datetime.timedelta(days=1)
        end_at = start_at + datetime.timedelta(hours=2)
        url = '/api/v1/events/'
        data = {
            'organization': self.org.id,
            'title': 'Grand Launching',
            'start_at': start_at.isoformat(),
            'end_at': end_at.isoformat(),
            'is_public': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        event_id = response.data['id']

        # 2. RSVP
        url_rsvp = f'/api/v1/events/{event_id}/attendance/'
        data_rsvp = {'status': 'going'}
        response_rsvp = self.client.post(url_rsvp, data_rsvp, format='json')
        # Depending on implementation, might return 200 or 201
        self.assertIn(response_rsvp.status_code, [200, 201])
