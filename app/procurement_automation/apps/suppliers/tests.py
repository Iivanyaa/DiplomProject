from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.users.models import User

class SupplierAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='supplier',
            email='supplier@example.com',
            password='Testpass123!',
            user_type='supplier'
        )
        self.client.force_authenticate(user=self.user)

    def test_supplier_profile(self):
        url = reverse('supplier-profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['email'], 'supplier@example.com')