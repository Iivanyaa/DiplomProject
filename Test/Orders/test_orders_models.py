import pytest
from django.db import IntegrityError
from Orders.models import Order, OrderProduct, SellerOrder
from Products.models import Product
from Users.models import MarketUser

@pytest.mark.django_db
class TestOrderModel:
    def test_create_order(self, buyer_user):
        order = Order.objects.create(
            user=buyer_user,
            total_price=100.00
        )
        assert order.user == buyer_user
        assert order.total_price == 100.00
        assert order.created_at is not None
        assert order.updated_at is not None

    def test_order_status_default(self, order, order_product):
        assert order.order_products.first().status == 'New'

@pytest.mark.django_db
class TestOrderProductModel:
    def test_create_order_product(self, order, product, buyer_user, seller_user):
        order_product = OrderProduct.objects.create(
            order=order,
            product=product,
            quantity=2,
            buyer=buyer_user,
            seller=seller_user,
            status='Packed'
        )
        assert order_product.order == order
        assert order_product.product == product
        assert order_product.quantity == 2
        assert order_product.buyer == buyer_user
        assert order_product.seller == seller_user
        assert order_product.status == 'Packed'
        assert order_product.created_at is not None
        assert order_product.updated_at is not None


@pytest.mark.django_db
class TestSellerOrderModel:
    def test_create_seller_order(self, order, seller_user):
        seller_order = SellerOrder.objects.create(
            order=order,
            seller=seller_user
        )
        assert seller_order.order == order
        assert seller_order.seller == seller_user
        assert seller_order.created_at is not None
        assert seller_order.updated_at is not None