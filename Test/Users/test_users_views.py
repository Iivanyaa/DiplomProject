import pytest
from django.urls import reverse
from rest_framework import status
from Users.models import MarketUser
from Test.Users.conftest import __all__

from django.contrib.auth.models import Permission

@pytest.mark.django_db
class TestUserRegisterView:
    url = reverse('BuyerRegister')

    def test_register_buyer_success(self, api_client):
        data = {
            'username': 'newbuyer',
            'password': 'testpass123',
            'email': 'newbuyer@example.com',
            'user_type': 'Buyer',
            'first_name': 'New',
            'last_name': 'Buyer',
            'phone_number': '+1234567890'
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert MarketUser.objects.filter(username='newbuyer').exists()
        user = MarketUser.objects.get(username='newbuyer')
        assert user.groups.filter(name='Buyer').exists()

    def test_register_seller_success(self, api_client):
        data = {
            'username': 'newseller',
            'password': 'testpass123',
            'email': 'newseller@example.com',
            'user_type': 'Seller'
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert MarketUser.objects.filter(username='newseller').exists()
        user = MarketUser.objects.get(username='newseller')
        assert user.groups.filter(name='Seller').exists()

    def test_register_invalid_data(self, api_client):
        data = {
            'username': '',
            'password': 'testpass123',
            'email': 'invalid-email'
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data
        assert 'email' in response.data

@pytest.mark.django_db
class TestLoginView:
    url = reverse('login')

    def test_login_success(self, api_client, buyer_user):
        data = {
            'username': 'buyer_user',
            'password': 'testpass123'
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'Успешная аутентификация' in response.data['message']

    def test_login_invalid_credentials(self, api_client, buyer_user):
        data = {
            'username': 'buyer_user',
            'password': 'wrongpassword'
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'неверные данные' in response.data['message']

    def test_login_missing_fields(self, api_client):
        data = {
            'username': 'buyer_user'
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

@pytest.mark.django_db
class TestLogoutView:
    url = reverse('logout')

    def test_logout_success(self, authenticated_buyer_client):
        response = authenticated_buyer_client.post(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert 'Успешный выход' in response.data['message']

@pytest.mark.django_db
class TestChangePasswordView:
    url = reverse('change_password')

    def test_change_password_success(self, authenticated_buyer_client, buyer_user):
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123'
        }
        response = authenticated_buyer_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        buyer_user.refresh_from_db()
        assert buyer_user.check_password('newpass123')

    def test_change_password_wrong_old_password(self, authenticated_buyer_client):
        data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass123'
        }
        response = authenticated_buyer_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Неверный старый пароль' in response.data['message']

    def test_change_password_same_password(self, authenticated_buyer_client):
        data = {
            'old_password': 'testpass123',
            'new_password': 'testpass123'
        }
        response = authenticated_buyer_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_unauthenticated(self, api_client):
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123'
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Пользователь не аутентифицирован' in response.data['message']

@pytest.mark.django_db
class TestDeleteUserView:
    url = reverse('delete_user')

    # Покупатель успешно удаляет свой профиль
    def test_delete_user_success(self, authenticated_buyer_client, buyer_user):
        response = authenticated_buyer_client.delete(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert not MarketUser.objects.filter(id=buyer_user.id).exists()

    # Админ успешно удаляет профиль покупателя по id
    def test_delete_user_by_id(self, authenticated_admin_client, buyer_user):
        data = {
            'id': buyer_user.id
        }
        response = authenticated_admin_client.delete(self.url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert not MarketUser.objects.filter(id=buyer_user.id).exists()

    # Админ успешно удаляет профиль покупателя по username
    def test_delete_user_by_username(self, authenticated_admin_client, buyer_user):
        data = {
            'username': buyer_user.username
        }
        response = authenticated_admin_client.delete(self.url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert not MarketUser.objects.filter(id=buyer_user.id).exists()

    # продавец безуспешно пытается удалить чужой профиль по id, но у него недостаточно прав
    def test_delete_user_insufficient_permissions(self, authenticated_seller_client, buyer_user):
        data = {
            'id': buyer_user.id
        }
        response = authenticated_seller_client.delete(self.url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Недостаточно прав' in response.data['message']

    # неавторизированный пользователь пытается удаляить себя, но у него недостаточно прав
    def test_delete_user_unauthenticated(self, api_client):
        response = api_client.delete(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Недостаточно прав' in response.data['message']



@pytest.mark.django_db
class TestUpdateUserView:
    url = reverse('update_user')

    def test_update_user_success(self, authenticated_buyer_client, buyer_user):
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone_number': '+9876543210'
        }
        response = authenticated_buyer_client.put(self.url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        buyer_user.refresh_from_db()
        assert buyer_user.first_name == 'Updated'
        assert buyer_user.last_name == 'Name'
        assert buyer_user.phone_number == '+9876543210'

    def test_update_user_by_id(self, authenticated_admin_client, buyer_user):
        data = {
            'id': buyer_user.id,
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone_number': '+9876543210'
        }
        response = authenticated_admin_client.put(self.url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        buyer_user.refresh_from_db()
        assert buyer_user.first_name == 'Updated'
        assert buyer_user.last_name == 'Name'
        assert buyer_user.phone_number == '+9876543210'

    def test_update_user_by_id_insufficient_permissions(self, authenticated_buyer_client, authenticated_seller_client, buyer_user):
       # продавец пытается обновить чужой профиль, но у него недостаточно прав
        data = {
            'id': buyer_user.id,
            'first_name': 'Updated'
        }
        response = authenticated_seller_client.put(self.url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'Недостаточно прав' in response.data['message']

    def test_update_user_by_id_not_found(self, authenticated_admin_client):
        data = {
            'id': 999,  # id пользователя, которого не существует
            'first_name': 'Updated'
        }
        response = authenticated_admin_client.put(self.url, data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'Пользователь не найден' in response.data['message']

    def test_update_user_by_id_unauthenticated(self, api_client):
        data = {
            'id': 1,  # id пользователя, который существует
            'first_name': 'Updated'
        }
        response = api_client.put(self.url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Пользователь не аутентифицирован' in response.data['message']

@pytest.mark.django_db
class TestDeleteUserDataView:
    url = reverse('delete_user_data')

    def test_delete_user_data_success(self, authenticated_buyer_client, buyer_user):
        buyer_user.phone_number = '+1234567890'
        buyer_user.save()
        
        # Удаляем данные текущего пользователя
        data = {
            'data_to_delete': ['phone_number']
        }
        response = authenticated_buyer_client.delete(self.url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        buyer_user.refresh_from_db()
        assert buyer_user.phone_number is None
    
    def test_delete_user_data_by_id_success(self, authenticated_admin_client, buyer_user):
        buyer_user.phone_number = '+1234567890'
        buyer_user.save()
        
        # Удаляем данные пользователя
        data = {
            'id': buyer_user.id,
            'data_to_delete': ['phone_number']
        }
        response = authenticated_admin_client.delete(self.url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        buyer_user.refresh_from_db()
        assert buyer_user.phone_number is None
        
    def test_delete_user_data_by_id_insufficient_permissions(self, authenticated_seller_client, buyer_user):
        # пользователь пытается удалить данные другого пользователя, но у него недостаточно прав
        data = {
            'id': buyer_user.id,
            'data_to_delete': ['phone_number']
        }
        response = authenticated_seller_client.delete(self.url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Недостаточно прав' in response.data['message']

    def test_delete_user_data_by_id_not_found(self, authenticated_admin_client):
        # пользователь пытается удалить данные несуществующего пользователя
        data = {
            'id': 999,
            'data_to_delete': ['phone_number']
        }
        response = authenticated_admin_client.delete(self.url, data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'Пользователь не найден' in response.data['message']

    def test_delete_user_data_unauthenticated(self, api_client):
        # не аутентифицированный пользователь пытается удалить данные
        data = {
            'data_to_delete': ['phone_number']
        }
        response = api_client.delete(self.url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Пользователь не аутентифицирован' in response.data['message']

@pytest.mark.django_db
class TestGetUserDataView:
    url = reverse('Get_User')

    def test_get_user_data_success(self, authenticated_buyer_client, buyer_user):
        buyer_user.first_name = 'Test'
        buyer_user.last_name = 'Grisha'
        buyer_user.phone_number = '+1234567890'
        buyer_user.save()
        
        response = authenticated_buyer_client.get(self.url, format='json')
        # Проверяем, что данные пользователя возвращаются в ожидаемом формате
        assert 'first_name' in response.data['данные пользователя']
        assert 'last_name' in response.data['данные пользователя'] 
        assert 'phone_number' in response.data['данные пользователя']  
        assert 'username' in response.data['данные пользователя']  

        # Проверяем, что данные пользователя соответствуют ожидаемым значениям
        assert response.status_code == status.HTTP_200_OK
        assert response.data['данные пользователя']['first_name'] == 'Test'
        assert response.data['данные пользователя']['last_name'] == 'Grisha'
        assert response.data['данные пользователя']['phone_number'] == '+1234567890'
        assert response.data['данные пользователя']['username'] == 'buyer_user'

    def test_get_user_data_by_id_success(self, authenticated_admin_client, buyer_user):
        buyer_user.first_name = 'Test'
        buyer_user.last_name = 'User'
        buyer_user.phone_number = '+1234567890'
        buyer_user.save()
        buyer_user.refresh_from_db()

        url = f"{self.url}?id={buyer_user.id}"

        response = authenticated_admin_client.get(url, format='json')
        # Проверяем, что данные пользователя возвращаются в ожидаемом формате
        assert 'first_name' in response.data['данные пользователя']
        assert 'last_name' in response.data['данные пользователя']
        assert 'phone_number' in response.data['данные пользователя']
        assert 'username' in response.data['данные пользователя']

        # Проверяем, что данные пользователя соответствуют ожидаемым значениям
        assert response.data['данные пользователя']['first_name'] == buyer_user.first_name
        assert response.data['данные пользователя']['last_name'] == buyer_user.last_name
        assert response.data['данные пользователя']['phone_number'] == buyer_user.phone_number
        assert response.data['данные пользователя']['username'] == buyer_user.username

    def test_get_user_data_by_id_insufficient_permissions(self, authenticated_seller_client, buyer_user):
        # пользователь пытается получить данные другого пользователя, но у него недостаточно прав
        data = {
            'id': buyer_user.id
        }
        response = authenticated_seller_client.get(self.url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Недостаточно прав' in response.data['message']

    def test_get_user_data_by_id_not_found(self, authenticated_admin_client):
        # пользователь пытается получить данные несуществующего пользователя
        data = {
            'id': 999
        }
        response = authenticated_admin_client.get(self.url, data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'Пользователь не найден' in response.data['message']

    def test_get_user_data_unauthenticated(self, api_client):
        # не аутентифицированный пользователь пытается получить данные
        response = api_client.get(self.url, format='json')
        assert 'Недостаточно прав' in response.data['message']
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
class TestRestorePasswordView:
    url = reverse('restore_password')

    def test_restore_password_success(self, api_client, buyer_user, mailoutbox):
        data = {
            'email': buyer_user.email
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert len(mailoutbox) == 1
        assert 'Восстановление пароля' in mailoutbox[0].subject
        assert buyer_user.email in mailoutbox[0].to

    def test_restore_password_invalid_email(self, api_client):
        data = {
            'email': 'nonexistent@example.com'
        }
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'Пользователь с таким электронным адресом не найден' in response.data['message']