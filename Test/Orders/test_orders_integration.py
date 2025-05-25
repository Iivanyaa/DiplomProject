import pytest
from django.urls import reverse
from rest_framework import status
from Orders.models import Order, OrderProduct
from Products.models import Product
from Users.models import MarketUser

@pytest.mark.django_db
class TestOrderWorkflow:
    @pytest.fixture(autouse=True)
    def setup(self, buyer_user, seller_user, product):
        self.url = reverse('Orders')
        self.buyer = buyer_user
        self.seller = seller_user
        self.product = product

    def test_full_order_workflow(self, authenticated_buyer_client, authenticated_seller_client):
        # 1. Create an order
        order = Order.objects.create(user=self.buyer, total_price=self.product.price * 2)
        order_product = OrderProduct.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            buyer=self.buyer,
            seller=self.seller,
            status='New'
        )

        # 2. Buyer views their orders
        response = authenticated_buyer_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['orders']) == 1
        assert response.data['orders'][0]['status'] == 'New'

        # 3. Seller updates order status to Packed
        data = {'id': order_product.id, 'status': 'Packed'}
        response = authenticated_seller_client.put(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'Packed'

        # 4. Seller updates order status to Shipped
        data = {'id': order_product.id, 'status': 'Shipped'}
        response = authenticated_buyer_client.put(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'Shipped'

        # 5. Buyer checks order status
        authenticated_buyer_client.force_authenticate(user=self.buyer)
        data = {'id': order_product.id}
        response = authenticated_buyer_client.get(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['orders'][0]['status'] == 'Shipped'

        # 6. Seller completes the order
        authenticated_buyer_client.force_authenticate(user=self.seller)
        data = {'id': order_product.id, 'status': 'Completed'}
        response = authenticated_buyer_client.put(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'Completed'

        # 7. Verify order is completed
        order_product.refresh_from_db()
        assert order_product.status == 'Completed'