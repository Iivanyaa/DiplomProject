# tests/products/test_models.py
import pytest
from django.db import IntegrityError
from Products.models import Product, Category, Cart, CartProduct

@pytest.mark.django_db
class TestProductModel:
    def test_create_product(self, seller_user):
        product = Product.objects.create(
            name="Test Product",
            price=100.00,
            description="Test Description",
            quantity=10,
            seller=seller_user
        )
        assert product.is_available is True
        assert str(product) == "Test Product"

    def test_product_availability(self):
        product = Product.objects.create(
            name="Test Product",
            price=100.00,
            description="Test Description",
            quantity=0
        )
        assert product.is_available is False

@pytest.mark.django_db
class TestCategoryModel:
    def test_create_category(self):
        category = Category.objects.create(name="Electronics")
        assert str(category) == "Electronics"

    def test_add_product_to_category(self, product):
        category = Category.objects.create(name="Electronics")
        category.products.add(product)
        assert category.products.count() == 1

@pytest.mark.django_db
class TestCartModel:
    def test_cart_creation(self, buyer_user):
        cart = Cart.objects.create(user=buyer_user)
        assert cart.TotalPrice() == 0

    def test_cart_total_price(self, cart, product):
        CartProduct.objects.create(cart=cart, product=product, quantity=2)
        assert cart.TotalPrice() == product.price * 2

    def test_unique_cart_per_user(self, buyer_user):
        Cart.objects.create(user=buyer_user)
        with pytest.raises(IntegrityError):
            Cart.objects.create(user=buyer_user)