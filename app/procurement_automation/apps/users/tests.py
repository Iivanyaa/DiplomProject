from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User

class UserAPITestCase(APITestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Testpass123!',
            'user_type': 'customer'
        }

    def test_user_registration(self):
        url = reverse('user-register')
        response = self.client.post(url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='test@example.com').exists())

    def test_jwt_authentication(self):
        User.objects.create_user(**self.user_data)
        url = reverse('token-obtain-pair')
        response = self.client.post(url, {
            'email': 'test@example.com',
            'password': 'Testpass123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)