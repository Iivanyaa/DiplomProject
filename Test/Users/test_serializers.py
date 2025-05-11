import pytest
from rest_framework.exceptions import ValidationError
from Users.serializers import (
    UserRegSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    DeleteUserSerializer,
    GetUserDataSerializer,
    DeleteUserDataSerializer,
    RestorePasswordSerializer
)

@pytest.mark.django_db
class TestUserRegSerializer:
    def test_valid_serializer_data(self):
        data = {
            'username': 'testuser',
            'password': 'testpass123',
            'email': 'test@example.com',
            'user_type': 'Buyer',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '+1234567890'
        }
        serializer = UserRegSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['username'] == 'testuser'
        assert serializer.validated_data['email'] == 'test@example.com'
        assert serializer.validated_data['user_type'] == 'Buyer'

    def test_invalid_serializer_data(self):
        data = {
            'username': '',
            'password': 'testpass123',
            'email': 'invalid-email',
            'user_type': 'InvalidType'
        }
        serializer = UserRegSerializer(data=data)
        assert not serializer.is_valid()
        assert 'username' in serializer.errors
        assert 'email' in serializer.errors
        assert 'user_type' in serializer.errors

    def test_create_user(self):
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'email': 'new@example.com',
            'user_type': 'Buyer'
        }
        serializer = UserRegSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        assert user.username == 'newuser'
        assert user.check_password('newpass123')
        assert user.email == 'new@example.com'
        assert user.user_type == 'Buyer'

@pytest.mark.django_db
class TestLoginSerializer:
    def test_valid_serializer_data(self):
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        serializer = LoginSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['username'] == 'testuser'
        assert serializer.validated_data['password'] == 'testpass123'

    def test_missing_fields(self):
        data = {
            'username': 'testuser'
        }
        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors

@pytest.mark.django_db
class TestChangePasswordSerializer:
    def test_valid_serializer_data(self):
        data = {
            'old_password': 'oldpass123',
            'new_password': 'newpass123'
        }
        serializer = ChangePasswordSerializer(data=data)
        assert serializer.is_valid()

    def test_same_passwords(self):
        data = {
            'old_password': 'samepass',
            'new_password': 'samepass'
        }
        serializer = ChangePasswordSerializer(data=data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors

@pytest.mark.django_db
class TestDeleteUserSerializer:
    def test_valid_serializer_data(self, buyer_user):
        data = {
            'user_id': buyer_user.id
        }
        serializer = DeleteUserSerializer(data=data)
        assert serializer.is_valid()

    def test_invalid_user_id(self):
        data = {
            'user_id': 9999  # Несуществующий ID
        }
        serializer = DeleteUserSerializer(data=data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors

@pytest.mark.django_db
class TestGetUserDataSerializer:
    def test_valid_serializer_data(self, buyer_user):
        data = {
            'user_id': buyer_user.id
        }
        serializer = GetUserDataSerializer(data=data)
        assert serializer.is_valid()

    def test_invalid_user_id(self):
        data = {
            'user_id': 9999  # Несуществующий ID
        }
        serializer = GetUserDataSerializer(data=data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors

@pytest.mark.django_db
class TestDeleteUserDataSerializer:
    def test_valid_serializer_data(self):
        data = {
            'data_to_delete': ['first_name', 'last_name']
        }
        serializer = DeleteUserDataSerializer(data=data)
        assert serializer.is_valid()

    def test_empty_data_to_delete(self):
        data = {
            'data_to_delete': []
        }
        serializer = DeleteUserDataSerializer(data=data)
        assert not serializer.is_valid()
        assert 'data_to_delete' in serializer.errors

@pytest.mark.django_db
class TestRestorePasswordSerializer:
    def test_valid_serializer_data(self, buyer_user):
        data = {
            'email': buyer_user.email
        }
        serializer = RestorePasswordSerializer(data=data)
        assert serializer.is_valid()

    def test_invalid_email(self):
        data = {
            'email': 'nonexistent@example.com'
        }
        serializer = RestorePasswordSerializer(data=data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors