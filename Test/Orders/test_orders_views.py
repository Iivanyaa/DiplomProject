import pytest
from django.urls import reverse
from rest_framework import status
from Orders.models import Order, OrderProduct
from Users.models import MarketUser
import requests

@pytest.mark.django_db
class TestOrderView:
    @pytest.fixture(autouse=True)
    def setup(self, buyer_user, seller_user, admin_user, product):
        self.url = reverse('Orders')
        self.buyer = buyer_user
        self.seller = seller_user
        self.admin = admin_user
        self.product = product

        # Create orders for testing
        self.order = Order.objects.create(user=self.buyer, total_price=100.00)
        self.order_product = OrderProduct.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            buyer=self.buyer,
            seller=self.seller,
            status='New'
        )

    def test_get_orders_as_buyer(self, authenticated_buyer_client):
        response = authenticated_buyer_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['orders']) == 1
        assert response.data['message'] == 'Все заказы'

    def test_get_orders_as_seller(self, authenticated_seller_client):
        response = authenticated_seller_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['orders']) == 1
        assert response.data['message'] == 'Все заказы'

    def test_get_orders_as_admin(self, authenticated_admin_client):
        response = authenticated_admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['orders']) == 1
        assert response.data['message'] == 'Все заказы'

    def test_get_orders_with_id_as_buyer(self, authenticated_buyer_client):
        data = {'id': self.order_product.id}
        response = authenticated_buyer_client.get(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Заказ найден'
        assert response.data['orders'][0]['id'] == self.order_product.id

    def test_get_nonexistent_order(self, authenticated_buyer_client):
        data = {'id': 1000}
        response = authenticated_buyer_client.get(self.url, data, format='json', application='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['message'] == 'Заказ не найден'

    def test_update_order_status(self, authenticated_seller_client):
        data = {'id': self.order_product.id, 'status': 'Shipped'}
        response = authenticated_seller_client.put(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Статус заказа успешно изменен'
        assert response.data['status'] == 'Shipped'

    def test_update_to_same_status(self, authenticated_seller_client):
        data = {'id': self.order_product.id, 'status': 'New'}
        response = authenticated_seller_client.put(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['message'] == 'Статус заказа не изменился'

    def test_cancel_order_restores_quantity(self, authenticated_admin_client, product):
        initial_quantity = product.quantity
        data = {'id': self.order_product.id, 'status': 'Canceled'}
        response = authenticated_admin_client.put(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert product.quantity == initial_quantity + self.order_product.quantity

    def test_update_order_status_unauthorized(self, api_client):
        data = {'id': self.order_product.id, 'status': 'Shipped'}
        response = api_client.put(self.url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['message'] == 'Недостаточно прав'

    def test_invalid_status_update(self, authenticated_seller_client):
        data = {'id': self.order_product.id, 'status': 'Invalid'}
        response = authenticated_seller_client.put(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'status' in response.data