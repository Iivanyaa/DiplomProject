import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
class TestUserWorkflow:
    def test_full_user_workflow(self, api_client):
        # 1. Регистрация пользователя
        register_url = reverse('BuyerRegister')
        register_data = {
            'username': 'workflow_user',
            'password': 'testpass123',
            'email': 'workflow@example.com',
            'user_type': 'Buyer'
        }
        register_response = api_client.post(register_url, register_data, format='json')
        assert register_response.status_code == status.HTTP_201_CREATED
        
        # 2. Вход пользователя
        login_url = reverse('login')
        login_data = {
            'username': 'workflow_user',
            'password': 'testpass123'
        }
        login_response = api_client.post(login_url, login_data, format='json')
        assert login_response.status_code == status.HTTP_200_OK
        
        # 3. Обновление данных пользователя
        update_url = reverse('update_user')
        update_data = {
            'first_name': 'Workflow',
            'last_name': 'User',
            'phone_number': '+1234567890'
        }
        # Для аутентификации используем force_authenticate, так как сессии не работают в тестах с APIClient
        from Users.models import MarketUser
        user = MarketUser.objects.get(username='workflow_user')
        api_client.force_authenticate(user=user)
        
        update_response = api_client.put(update_url, update_data, format='json')
        assert update_response.status_code == status.HTTP_200_OK
        
        # 4. Получение данных пользователя
        get_data_url = reverse('Get_User')
      
        get_data_response = api_client.get(get_data_url, format='json')
        assert get_data_response.status_code == status.HTTP_200_OK
        assert get_data_response.data['данные пользователя']['first_name'] == 'Workflow'
        assert get_data_response.data['данные пользователя']['last_name'] == 'User'
        
        # 5. Смена пароля
        change_password_url = reverse('change_password')
        change_password_data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123'
        }
        change_password_response = api_client.post(change_password_url, change_password_data, format='json')
        assert change_password_response.status_code == status.HTTP_200_OK
        
        # 6. Выход из системы
        logout_url = reverse('logout')
        logout_response = api_client.post(logout_url)
        assert logout_response.status_code == status.HTTP_200_OK
        
        # 7. Попытка входа со старым паролем должна провалиться
        failed_login_response = api_client.post(login_url, login_data, format='json')
        assert failed_login_response.status_code == status.HTTP_400_BAD_REQUEST
        
        # 8. Вход с новым паролем
        new_login_data = {
            'username': 'workflow_user',
            'password': 'newpass123'
        }
        new_login_response = api_client.post(login_url, new_login_data, format='json')
        assert new_login_response.status_code == status.HTTP_200_OK