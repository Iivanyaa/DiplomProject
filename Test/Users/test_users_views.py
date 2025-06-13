import pytest
from django.urls import reverse
from rest_framework import status
from Users.models import MarketUser, Contact, UserGroup
from Test.Users.conftest import *
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from Users.serializers import *
from django.core.cache import cache

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
        assert 'username' in response.data['errors'].keys()
        assert 'email' in response.data['errors'].keys()

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
        response = authenticated_buyer_client.delete(f"{self.url}?id={buyer_user.id}")
        assert response.status_code == status.HTTP_200_OK
        assert not MarketUser.objects.filter(id=buyer_user.id).exists()

    # Админ успешно удаляет профиль покупателя по id
    def test_delete_user_by_id(self, authenticated_admin_client, buyer_user):
        response = authenticated_admin_client.delete(f"{self.url}?id={buyer_user.id}")
        assert response.status_code == status.HTTP_200_OK
        assert not MarketUser.objects.filter(id=buyer_user.id).exists()

    # Админ успешно удаляет профиль покупателя по username
    def test_delete_user_by_username(self, authenticated_admin_client, buyer_user):
        response = authenticated_admin_client.delete(f"{self.url}?username={buyer_user.username}")
        assert response.status_code == status.HTTP_200_OK
        assert not MarketUser.objects.filter(id=buyer_user.id).exists()

    # продавец безуспешно пытается удалить чужой профиль по id, но у него недостаточно прав
    def test_delete_user_insufficient_permissions(self, authenticated_seller_client, buyer_user):
        response = authenticated_seller_client.delete(f"{self.url}?id={buyer_user.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Недостаточно прав' in response.data['message']

    # неавторизированный пользователь пытается удаляить себя, но у него недостаточно прав
    def test_delete_user_unauthenticated(self, api_client, buyer_user):
        response = api_client.delete(f"{self.url}?id={buyer_user.id}")
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
        response = authenticated_buyer_client.delete(f"{self.url}?data_to_delete=phone_number", format='json')
        assert response.status_code == status.HTTP_200_OK
        buyer_user.refresh_from_db()
        assert buyer_user.phone_number is None
    
    def test_delete_user_data_by_id_success(self, authenticated_admin_client, buyer_user):
        buyer_user.phone_number = '+1234567890'
        buyer_user.save()
        
        # Удаляем данные пользователя
        response = authenticated_admin_client.delete(f"{self.url}?id={buyer_user.id}&data_to_delete=phone_number", format='json')
        assert response.status_code == status.HTTP_200_OK
        buyer_user.refresh_from_db()
        assert buyer_user.phone_number is None
        
    def test_delete_user_data_by_id_insufficient_permissions(self, authenticated_seller_client, buyer_user):
        # пользователь пытается удалить данные другого пользователя, но у него недостаточно прав
        response = authenticated_seller_client.delete(f"{self.url}?id={buyer_user.id}&data_to_delete=phone_number", format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Недостаточно прав' in response.data['message']

    def test_delete_user_data_by_id_not_found(self, authenticated_admin_client):
        # пользователь пытается удалить данные несуществующего пользователя
        response = authenticated_admin_client.delete(f"{self.url}?id=999&data_to_delete=phone_number", format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'Пользователь не найден' in response.data['message']

    def test_delete_user_data_unauthenticated(self, api_client):
        # не аутентифицированный пользователь пытается удалить данные
        response = api_client.delete(f"{self.url}?data_to_delete=phone_number", format='json')
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

@pytest.mark.django_db
class TestAddContactView:
    # URL для AddContactView
    url = reverse('contacts') # Замените 'contacts' на фактическое имя вашего URL-адреса

    def test_add_contact_success(self, authenticated_buyer_client, buyer_user, contact_data):
        # Проверка успешного добавления контакта
        response = authenticated_buyer_client.post(self.url, contact_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'Контакт успешно добавлен' in response.data['message']
        assert buyer_user.contacts.count() == 1
        assert buyer_user.contacts.first().phone == contact_data['phone']

    def test_add_contact_unauthenticated(self, api_client, contact_data):
        # Проверка добавления контакта неаутентифицированным пользователем
        data = contact_data
        response = api_client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Недостаточно прав' in response.data['message']

    def test_add_contact_insufficient_permissions(self, authenticated_buyer_client, buyer_user, contact_data):
        # Проверка добавления контакта без необходимых прав
        # Удаляем разрешение на добавление контакта у пользователя
        content_type = ContentType.objects.get_for_model(MarketUser)
        buyer_group = UserGroup.objects.get(name='Buyer')
        buyer_group.permissions.clear()
        buyer_user.save()

        response = authenticated_buyer_client.post(self.url, contact_data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED # Или HTTP_403_FORBIDDEN, в зависимости от AccessCheck
        assert 'Недостаточно прав' in response.data['message']

    def test_add_contact_max_limit_exceeded(self, authenticated_buyer_client, buyer_user, contact_data):
        # Проверка добавления контакта при превышении максимального лимита (5 контактов)
        for i in range(5):
            Contact.objects.create(user=buyer_user, city=f'City{i}', street=f'Street{i}', phone=f'+7900000000{i}')
        
        response = authenticated_buyer_client.post(self.url, contact_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Превышено максимальное количество контактов' in response.data['message']
        assert buyer_user.contacts.count() == 5 # Убеждаемся, что новый контакт не добавлен

    def test_add_contact_invalid_data(self, authenticated_buyer_client):
        # Проверка добавления контакта с невалидными данными (например, отсутствует обязательное поле)
        invalid_data = {'city': 'TestCity'} # Отсутствует 'street' и 'phone'
        response = authenticated_buyer_client.post(self.url, invalid_data, format='json')
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY # Или HTTP_400_BAD_REQUEST, в зависимости от raise_exception
        assert 'message' in response.data and response.data['message'] == 'Обязательные поля не заполнены' 

    def test_change_contact_success(self, authenticated_buyer_client, buyer_user, create_contact):
        # Проверка успешного изменения контакта
        print(create_contact.id)
        updated_data = {'id': create_contact.id, 'phone': '+79998887766', 'city': 'Новый Город'}
        print(updated_data)
        response = authenticated_buyer_client.put(self.url, updated_data, format='json')
        print(response.data)
        assert response.status_code == status.HTTP_200_OK
        assert 'Контакт успешно изменен' in response.data['message']
        create_contact.refresh_from_db() # Обновляем объект из базы данных
        assert create_contact.phone == updated_data['phone']
        assert create_contact.city == updated_data['city']

    def test_change_contact_unauthenticated(self, api_client, create_contact):
        # Проверка изменения контакта неаутентифицированным пользователем
        updated_data = {'id': create_contact.id, 'phone': '+79998887766'}
        response = api_client.put(self.url, updated_data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Недостаточно прав' in response.data['message']

    def test_change_contact_insufficient_permissions(self, authenticated_buyer_client, buyer_user, create_contact):
        # Проверка изменения контакта без необходимых прав
        buyer_group = UserGroup.objects.get(name='Buyer')
        buyer_group.permissions.clear()

        updated_data = {'id': create_contact.id, 'phone': '+79998887766'}
        response = authenticated_buyer_client.put(self.url, updated_data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED # Или HTTP_403_FORBIDDEN
        assert 'Недостаточно прав' in response.data['message']

    def test_change_contact_not_found(self, authenticated_buyer_client):
        # Проверка изменения несуществующего контакта
        updated_data = {'id': 9999, 'phone': '+79998887766'} # Несуществующий ID
        response = authenticated_buyer_client.put(self.url, updated_data, format='json')
        # В зависимости от реализации, это может быть 400, 404 или 200 с сообщением об отсутствии изменений
        # Предполагаем, что фильтр не найдет и update не сработает
        assert response.status_code == status.HTTP_404_NOT_FOUND # Если update() на пустом QuerySet просто ничего не делает
        assert 'Контакт не найден' in response.data['message'] # Если сообщение всегда возвращается
        # Более точная проверка:
        # assert not Contact.objects.filter(id=9999).exists() # Если бы была проверка на существование

    def test_delete_contact_success(self, authenticated_buyer_client, buyer_user, create_contact):
        # Проверка успешного удаления контакта
        initial_count = buyer_user.contacts.count()
        response = authenticated_buyer_client.delete(self.url, {'id': create_contact.id}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'Контакт успешно удален' in response.data['message']
        assert buyer_user.contacts.count() == initial_count - 1
        assert not Contact.objects.filter(id=create_contact.id).exists()

    def test_delete_contact_unauthenticated(self, api_client, create_contact):
        # Проверка удаления контакта неаутентифицированным пользователем
        response = api_client.delete(self.url, {'id': create_contact.id}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Недостаточно прав' in response.data['message']

    def test_delete_contact_insufficient_permissions(self, authenticated_buyer_client, buyer_user, create_contact):
        # Проверка удаления контакта без необходимых прав
        content_type = ContentType.objects.get_for_model(MarketUser)
        buyer_group = UserGroup.objects.get(name='Buyer')
        buyer_group.permissions.clear()

        response = authenticated_buyer_client.delete(self.url, {'id': create_contact.id}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED # Или HTTP_403_FORBIDDEN
        assert 'Недостаточно прав' in response.data['message']

    def test_delete_contact_not_found(self, authenticated_buyer_client):
        # Проверка удаления несуществующего контакта
        response = authenticated_buyer_client.delete(self.url, {'id': 9999}, format='json') # Несуществующий ID
        assert response.status_code == status.HTTP_404_NOT_FOUND 
        assert 'Контакт не найден' in response.data['message'] # Если сообщение всегда возвращается

    def test_get_all_contacts_success(self, authenticated_buyer_client, buyer_user):
        # Проверка получения всех контактов
        contact1 = Contact.objects.create(user=buyer_user, city='City1', street='Street1', phone='111')
        contact2 = Contact.objects.create(user=buyer_user, city='City2', street='Street2', phone='222')

        response = authenticated_buyer_client.get(self.url) # Запрос без ID
        assert response.status_code == status.HTTP_200_OK
        assert 'contacts' in response.data
        assert len(response.data['contacts']) == 2
        # Проверяем, что данные сериализованы правильно
        assert response.data['contacts'][0]['phone'] == contact1.phone
        assert response.data['contacts'][1]['phone'] == contact2.phone


    def test_get_single_contact_success(self, authenticated_buyer_client, buyer_user, create_contact):
        # Проверка получения конкретного контакта по ID
        response = authenticated_buyer_client.get(self.url, {'id': create_contact.id})
        assert response.status_code == status.HTTP_200_OK
        assert 'contact' in response.data
        assert response.data['contact']['phone'] == create_contact.phone
        assert response.data['contact']['city'] == create_contact.city

    def test_get_contact_unauthenticated(self, api_client, contact_data):
        # Проверка получения контактов неаутентифицированным пользователем
        data = contact_data
        response = api_client.get(self.url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Недостаточно прав' in response.data['message']

    def test_get_contact_insufficient_permissions(self, authenticated_buyer_client, buyer_user):
        # Проверка получения контактов без необходимых прав
        buyer_group = UserGroup.objects.get(name='Buyer')
        buyer_group.permissions.clear()

        response = authenticated_buyer_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED # Или HTTP_403_FORBIDDEN
        assert 'Недостаточно прав' in response.data['message']

    def test_get_single_contact_not_found(self, authenticated_buyer_client):
        # Проверка получения несуществующего контакта по ID
        response = authenticated_buyer_client.get(self.url, {'id': 9999})
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'Контакт не найден' in response.data['message']

 
@pytest.mark.django_db
class TestThrottling:
    # URL для AddContactView
    url = reverse('Get_User') # Замените 'contacts' на фактическое имя вашего URL-адреса
    def test_get_user_data_throttling_authenticated(self, authenticated_buyer_client):
        cache.clear()
        url = reverse('Get_User')
        for _ in range(160):
            response = authenticated_buyer_client.get(url)
            print(f"запрос {_} Status code: {response.status_code}")
            print(response.status_code)
            if _ < 150:
                assert response.status_code == status.HTTP_200_OK
            else:
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_get_user_data_throttling_unauthenticated(self, api_client):
        cache.clear()
        url = reverse('Get_User')
        for _ in range(121):
            response = api_client.get(url)
            print(f"запрос {_} Status code: {response.status_code}")
            print(response.status_code)
            if _ < 120:
                assert response.status_code == status.HTTP_401_UNAUTHORIZED
            else:
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

