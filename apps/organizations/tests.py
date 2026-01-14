from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class OrganizationTests(APITestCase):
    def setUp(self):
        # Create user and login
        self.user = User.objects.create_user(username='testorg', email='org@test.com', password='password')
        # Simulate Getting Token (Mocking or just force login if using Session, but we are API. 
        # Better to just self.client.force_authenticate if DRF supports it, usually does)
        self.client.force_authenticate(user=self.user)

    def test_create_and_list_orgs(self):
        # 1. Create Org
        url = '/api/v1/orgs/'
        data = {
            'name': 'BEM Kema',
            'description': 'Badan Eksekutif Mahasiswa'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'BEM Kema')
        slug = response.data['slug']

        # 2. List Orgs
        url_list = '/api/v1/public/organizations'
        response_list = self.client.get(url_list)
        self.assertEqual(response_list.status_code, 200)
        # Check if result is paginated or list
        results = response_list.data.get('results', response_list.data)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]['name'], 'BEM Kema')
