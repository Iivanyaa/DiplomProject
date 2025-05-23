# tests/products/test_views.py
import pytest
from django.urls import reverse
from rest_framework import status
from Products.models import Product, Category, CartProduct, Cart

@pytest.mark.django_db
class TestProductsView:
    @pytest.fixture(autouse=True)
    def setup(self, product, category):
        self.url = reverse('Products')
        self.product = product
        self.category = category

    def test_get_all_products(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['products']) == 1

    def test_create_product_as_seller(self, authenticated_seller_client):
        data = {
            "name": "New Product",
            "price": 199.99,
            "description": "New Description",
            "quantity": 10
        }
        response = authenticated_seller_client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Product.objects.count() == 2

    def test_create_product_unauthorized(self, api_client):
        response = api_client.post(self.url, {
            "name": "New Product",
            "price": 199.99,
            "description": "New Description",
            "quantity": 10
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['message'] == 'Недостаточно прав'

    def test_update_product(self, authenticated_seller_client):
        data = {
            "id": self.product.id,
            "price": '150.00',
            "description": "Updated Description"
        }
        response = authenticated_seller_client.put(self.url, data)
        self.product.refresh_from_db()
        assert self.product.price == 150.00
        assert response.status_code == status.HTTP_200_OK
        assert self.product.description == "Updated Description"
        assert self.product.is_available is True

    def test_delete_product(self, authenticated_seller_client):
        # Проверяем существование продукта
        assert Product.objects.filter(id=self.product.id).exists()
    
        # Отправляем DELETE-запрос с параметром в URL
        response = authenticated_seller_client.delete(
            f"{self.url}?id={self.product.id}",
            format='json'
        )
    
        # Проверяем статус и отсутствие продукта
        assert response.status_code == status.HTTP_200_OK
        assert not Product.objects.filter(id=self.product.id).exists()

@pytest.mark.django_db
class TestCategoriesView:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.url = reverse('Categories')

    def test_create_category_as_admin(self, authenticated_admin_client):
        data = {"name": "New Category"}
        response = authenticated_admin_client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Category.objects.count() == 1

    def test_delete_category(self, category, authenticated_admin_client):
        data = {"id": category.id}
        response = authenticated_admin_client.delete(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        assert Category.objects.count() == 0

@pytest.mark.django_db
class TestCartView:
    @pytest.fixture(autouse=True)
    def setup(self, buyer_user, product):
        self.url = reverse('Cart')
        self.buyer = buyer_user
        self.product = product

    def test_add_to_cart(self, authenticated_buyer_client):
        data = {"id": self.product.id, "quantity": 2}
        response = authenticated_buyer_client.patch(reverse('Products'), data)
        assert response.status_code == status.HTTP_200_OK
        assert CartProduct.objects.count() == 1

    def test_get_cart(self, authenticated_buyer_client):
        response = authenticated_buyer_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert 'Cart_products' in response.data

    def test_checkout_cart(self, authenticated_buyer_client):
        # Добавляем товар в корзину
        cart, _ = Cart.objects.get_or_create(user=self.buyer)
        CartProduct.objects.create(
            cart=Cart.objects.get(user=self.buyer),
            product=self.product,
            quantity=10
        )
        response = authenticated_buyer_client.post(self.url)
        assert response.status_code == status.HTTP_201_CREATED
        self.product.refresh_from_db()
        assert self.product.quantity == 0  # Исходное количество было 10
        assert self.product.is_available is False

    def test_remove_from_cart(self, authenticated_buyer_client):
        # Создаем корзину и добавляем товар
        cart, _ = Cart.objects.get_or_create(user=self.buyer)
        CartProduct.objects.create(cart=cart, product=self.product, quantity=1)

        # Проверяем, что товар в корзине
        assert cart.products.count() == 1

        # Отправляем DELETE-запрос
        data = {"id": self.product.id}
        response = authenticated_buyer_client.delete(
            reverse('Cart'),
            data,
            format='json'
        )

        # Проверяем ответ и состояние корзины
        assert response.status_code == status.HTTP_200_OK
        assert cart.products.count() == 0