import pytest
import requests
from django.contrib.auth.models import Group
from Products.models import Product, Category, Cart, CartProduct
from Users.models import MarketUser, UserGroup, Contact

# @pytest.fixture
# def buyer_group(db):
#     group, _ = UserGroup.objects.get_or_create(name='Buyer')
#     return group

# @pytest.fixture
# def seller_group(db):
#     group, _ = UserGroup.objects.get_or_create(name='Seller')
#     return group

# @pytest.fixture
# def admin_group(db):
#     group, _ = UserGroup.objects.get_or_create(name='Admin')
#     return group

@pytest.fixture
def buyer_user(db, buyer_group):
    user = MarketUser.objects.create_user(
        username='buyer_user',
        password='testpass123',
        email='buyer@example.com',
        user_type='Buyer'
    )
    buyer_group.user_set.add(user)
    
    return user

@pytest.fixture
def seller_user(db, seller_group):
    user = MarketUser.objects.create_user(
        username='seller_user',
        password='testpass123',
        email='seller@example.com',
        user_type='Seller'
    )
    seller_group.user_set.add(user)
    return user

@pytest.fixture
def admin_user(db, admin_group):
    user = MarketUser.objects.create_user(
        username='admin_user',
        password='testpass123',
        email='admin@example.com',
        user_type='Admin'
    )
    admin_group.user_set.add(user)
    return user

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def authenticated_buyer_client(api_client, buyer_user):
    api_client.force_authenticate(user=buyer_user)
    session = api_client.session
    session['user_id'] = buyer_user.id
    session['user_type'] = buyer_user.user_type
    session['username'] = buyer_user.username
    session.save()
    return api_client

@pytest.fixture
def authenticated_seller_client(api_client, seller_user):
    api_client.force_authenticate(user=seller_user)
    session = api_client.session
    session['user_id'] = seller_user.id
    session['user_type'] = seller_user.user_type
    session['username'] = seller_user.username
    session.save()
    return api_client

@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    session = api_client.session
    session['user_id'] = admin_user.id
    session['user_type'] = admin_user.user_type
    session['username'] = admin_user.username
    session.save()
    return api_client


@pytest.fixture
def product(seller_user):
    return Product.objects.create(
        name="Test Product",
        price=100.00,
        description="Test Description",
        quantity=10,
        seller=seller_user
    )

@pytest.fixture
def category(db):
    return Category.objects.create(name="Test Category")

@pytest.fixture
def cart(buyer_user):
    return Cart.objects.create(user=buyer_user)

@pytest.fixture
def contact_data():
    # Данные для создания контакта
    return {
        'city': 'Москва',
        'street': 'Ленина',
        'house': '10',
        'structure': 'А',
        'building': '2',
        'apartment': '5',
        'phone': '+79001234567'
    }

@pytest.fixture
def create_contact(db, buyer_user, contact_data):
    # Фикстура для создания контакта, привязанного к пользователю
    contact = Contact.objects.create(user=buyer_user, **contact_data)
    return contact






__all__ = [
    # 'buyer_group',
    # 'seller_group',
    # 'admin_group',
    'buyer_user',
    'seller_user',
    'admin_user',
    'api_client',
    'authenticated_buyer_client',
    'authenticated_seller_client',
    'authenticated_admin_client',
    'product',
    'category',
    'cart',
    'contact_data',
    'create_contact'
]

