from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization

User = get_user_model()

class ContentTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='contentuser', email='content@test.com', password='password')
        self.client.force_authenticate(user=self.user)
        self.org = Organization.objects.create(name='Content Org', description='Desc', slug='content-org')

    def test_announcements_and_news(self):
        # 1. Create Announcement
        url_anno = '/api/v1/announcements/'
        data_anno = {
            'organization': self.org.id,
            'title': 'Internal Meeting',
            'content': 'Discussing proker.',
            'pinned': True
        }
        response = self.client.post(url_anno, data_anno, format='json')
        self.assertEqual(response.status_code, 201)

        # 2. Create News
        url_news = '/api/v1/news/'
        data_news = {
            'organization': self.org.id,
            'title': 'Open Recruitment',
            'content': 'We are hiring.',
            'status': 'published'
        }
        response = self.client.post(url_news, data_news, format='json')
        self.assertEqual(response.status_code, 201)
