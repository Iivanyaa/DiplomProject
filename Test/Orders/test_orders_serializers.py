import pytest
from rest_framework.exceptions import ValidationError
from Orders.serializers import (
    OrderSearchSerializer,
    OrderProductSerializer,
    OrderStatusUpdateSerializer
)

@pytest.mark.django_db
class TestOrderSearchSerializer:
    def test_valid_data(self):
        data = {'id': 1}
        serializer = OrderSearchSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['id'] == 1

    def test_empty_data(self):
        data = {}
        serializer = OrderSearchSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == {}

    def test_invalid_fields(self):
        data = {'id': 1, 'invalid_field': 'value'}
        serializer = OrderSearchSerializer(data=data)
        assert not serializer.is_valid()
        assert 'Недопустимые поля' in str(serializer.errors['non_field_errors'][0])

@pytest.mark.django_db
class TestOrderProductSerializer:
    def test_valid_data(self):
        data = {
            'product': '1',
            'buyer': '1',
            'seller': '1',
            'quantity': 2,
            'status': 'New',
            'id': 1
        }
        serializer = OrderProductSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['quantity'] == 2

    def test_missing_required_fields(self):
        data = {'quantity': 2}
        serializer = OrderProductSerializer(data=data)
        assert not serializer.is_valid()
        assert 'product' in serializer.errors
        assert 'buyer' in serializer.errors
        assert 'seller' in serializer.errors

    def test_invalid_quantity(self):
        data = {
            'product': '1',
            'buyer': '1',
            'seller': '1',
            'quantity': -1
        }
        serializer = OrderProductSerializer(data=data)
        assert not serializer.is_valid()
        assert 'quantity' in serializer.errors

@pytest.mark.django_db
class TestOrderStatusUpdateSerializer:
    def test_valid_data(self):
        data = {'id': 1, 'status': 'Packed'}
        serializer = OrderStatusUpdateSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['status'] == 'Packed'

    def test_invalid_status(self):
        data = {'id': 1, 'status': 'Invalid'}
        serializer = OrderStatusUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'status' in serializer.errors

    def test_missing_status(self):
        data = {'id': 1}
        serializer = OrderStatusUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'status' in serializer.errors