from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
import uuid
from apps.organizations.models import Organization

User = get_user_model()

class FinanceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='financeuser', email='finance@test.com', password='password')
        self.client.force_authenticate(user=self.user)
        self.org = Organization.objects.create(name='Finance Org', description='Desc', slug='finance-org')

    def test_web3_payment_flow(self):
        # 1. Submit Payment
        url_submit = f'/api/v1/orgs/{self.org.id}/finance/web3/submit'
        data = {
            'tx_hash': f'0xTestHash{uuid.uuid4().hex[:6]}',
            'wallet_address': '0xABC123',
            'amount_wei': '50000000000000000',
            'note': 'Montly Dues'
        }
        response = self.client.post(url_submit, data, format='json')
        self.assertEqual(response.status_code, 201)
        payment_id = response.data['id']

        # 2. Verify Payment
        url_verify = f'/api/v1/orgs/{self.org.id}/finance/web3/verify/{payment_id}'
        response_verify = self.client.post(url_verify, {})
        self.assertEqual(response_verify.status_code, 200)

        # 3. List My Payments
        url_list = f'/api/v1/orgs/{self.org.id}/finance/web3/my-payments'
        response_list = self.client.get(url_list)
        self.assertEqual(response_list.status_code, 200)
        self.assertTrue(len(response_list.data) > 0)
