import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from Users.models import MarketUser, UserGroup

@pytest.mark.django_db
class TestMarketUserModel:
    def test_create_buyer_user(self, buyer_user):
        assert buyer_user.username == 'buyer_user'
        assert buyer_user.user_type == 'Buyer'
        assert buyer_user.check_password('testpass123')
        assert buyer_user.email == 'buyer@example.com'
        assert buyer_user.groups.filter(name='Buyer').exists()
        assert buyer_user.is_active is True
        assert buyer_user.is_staff is False
        assert buyer_user.is_superuser is False

    def test_create_seller_user(self, seller_user):
        assert seller_user.username == 'seller_user'
        assert seller_user.user_type == 'Seller'
        assert seller_user.check_password('testpass123')
        assert seller_user.email == 'seller@example.com'
        assert seller_user.groups.filter(name='Seller').exists()
        assert seller_user.is_active is True
        assert seller_user.is_staff is False
        assert seller_user.is_superuser is False

    def test_create_admin_user(self, admin_user):
        assert admin_user.username == 'admin_user'
        assert admin_user.user_type == 'Admin'
        assert admin_user.check_password('testpass123')
        assert admin_user.email == 'admin@example.com'
        assert admin_user.groups.filter(name='Admin').exists()
        assert admin_user.is_active is True
        assert admin_user.is_staff is False
        assert admin_user.is_superuser is False

    def test_user_str_method(self, buyer_user):
        assert str(buyer_user) == 'buyer_user'

    # def test_access_check_method(self, buyer_user):
    #     from django.test import RequestFactory
    #     factory = RequestFactory()
    #     request = factory.get('/')
    #     request.session = {'user_id': buyer_user.id}
        
    #     # Добавляем разрешение для теста
    #     perm = Permission.objects.get(codename='change_password')
    #     buyer_user.user_permissions.add(perm)
        
    #     assert buyer_user.AccessCheck(request, 'Users.change_password') is True
    #     assert buyer_user.AccessCheck(request, 'Users.non_existent_perm') is False

@pytest.mark.django_db
class TestUserGroupModel:
    def test_user_group_creation(self, buyer_group):
        assert isinstance(buyer_group, UserGroup)
        assert str(buyer_group) == 'Buyer'
        assert buyer_group.name == 'Buyer'