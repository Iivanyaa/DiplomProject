import pytest
from django.contrib.auth.models import Group
from Users.models import MarketUser, UserGroup

@pytest.fixture
def buyer_group(db):
    group, _ = UserGroup.objects.get_or_create(name='Buyer')
    return group

@pytest.fixture
def seller_group(db):
    group, _ = UserGroup.objects.get_or_create(name='Seller')
    return group

@pytest.fixture
def admin_group(db):
    group, _ = UserGroup.objects.get_or_create(name='Admin')
    return group

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
    api_client.post(path=reversed('login'), data={'username': 'seller_user.username', 'password': 'seller_user.password'}, format='json')
    session = api_client.session
    session['user_id'] = seller_user.id
    session['user_type'] = seller_user.user_type
    session['username'] = seller_user.username
    session.save()
    return api_client

@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    api_client.post(path=reversed('login'), data={'username': 'admin_user.username', 'password': 'admin_user.password'}, format='json')
    session = api_client.session
    session['user_id'] = admin_user.id
    session['user_type'] = admin_user.user_type
    session['username'] = admin_user.username
    session.save()
    return api_client


__all__ = [
    'buyer_group',
    'seller_group',
    'admin_group',
    'buyer_user',
    'seller_user',
    'admin_user',
    'api_client',
    'authenticated_buyer_client',
    'authenticated_seller_client',
    'authenticated_admin_client',
]
