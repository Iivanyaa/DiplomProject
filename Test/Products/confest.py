# conftest.py (дополнение для Products)
import pytest
from Products.models import Product, Category
from Users.models import MarketUser

@pytest.fixture
def seller_user(db):
    return MarketUser.objects.create_user(
        username='seller',
        password='testpass',
        user_type='Seller'
    )

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
def authenticated_seller_client(api_client, seller_user):
    api_client.force_authenticate(user=seller_user)
    return api_client