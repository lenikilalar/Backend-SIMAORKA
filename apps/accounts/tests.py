from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from typing import cast, Any

User = get_user_model()

class AuthTests(APITestCase):
    def test_google_login_and_me(self):
        # 1. Login
        url = reverse('google-login') # Assuming URL name is 'google-login', checking urls.py might be needed but assuming standard convention based on views
        # If url name unknown, use path: '/api/v1/auth/google'
        url = '/api/v1/auth/google'
        
        data = {'id_token': 'testuser@example.com'}
        response = cast(Any, self.client).post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        
        token = response.data['access']
        
        # 2. Me
        cast(Any, self.client).credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        url_me = '/api/v1/me'
    def test_register_and_login(self):
        # 1. Register
        url_register = '/api/v1/auth/register'
        data_register = {
            'email': 'newuser@example.com',
            'password': 'securepassword123',
            'full_name': 'New User',
            'nim': '1234567890',
            'faculty': 'Fasilkom',
            'major': 'Sistem Informasi',
            'entry_year': 2024
        }
        response = cast(Any, self.client).post(url_register, data_register, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')
        self.assertIn('access', response.data)

        # 2. Login
        url_login = '/api/v1/auth/login'
        data_login = {
             'email': 'newuser@example.com',
             'password': 'securepassword123'
        }
        response_login = cast(Any, self.client).post(url_login, data_login, format='json')
        self.assertEqual(response_login.status_code, 200)
        self.assertIn('access', response_login.data)
        
        token = response_login.data['access']
        
        # 3. Check Profile
        cast(Any, self.client).credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        url_me = '/api/v1/me'
        response_me = cast(Any, self.client).get(url_me)
        self.assertEqual(response_me.status_code, 200)
        self.assertEqual(response_me.data['profile']['nim'], '1234567890')
