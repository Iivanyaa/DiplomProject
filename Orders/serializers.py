from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from Products.models import Product
from .models import Order, OrderProduct, ORDER_STATUS
from Users.models import MarketUser


class OrderSearchSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True) # allow_null=True - позволяет сериализатору принять None как значение, т.е. поле может быть пустым
    

    def validate(self, data):
        # Получаем все ключи из исходных данных
        received_keys = set(self.initial_data.keys())
        # Получаем ключи, объявленные в сериализаторе
        allowed_keys = set(self.fields.keys())
        # Находим неизвестные ключи
        unknown_keys = received_keys - allowed_keys
        # Проверяем наличие неизвестных ключей
        if unknown_keys:
            raise ValidationError(
                f"Недопустимые поля: {', '.join(unknown_keys)}. "
                f"Допустимые поля: {', '.join(allowed_keys)}."
            )
        
        attrs = super().validate(data)
        # # Проверяем, что хотя бы одно поле передано
        # if not attrs.get('id') and not attrs.get('name'):
        #     raise ValidationError("Укажите id или name для поиска.")

        # Проверяем, что не передано более одного параметра
        # if len([key for key, value in attrs.items() if value is not None]) > 1:
        #     raise ValidationError('Укажите только один параметр')
        
        return attrs


class OrderProductSerializer(serializers.Serializer):
    product = serializers.CharField(required=True)
    buyer = serializers.CharField(required=True)
    seller = serializers.CharField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=0)
    status = serializers.CharField(required=False, allow_null=True)
    id = serializers.IntegerField(required=False, allow_null=True)


class OrderStatusUpdateSerializer(OrderSearchSerializer):
    status = serializers.ChoiceField(required=True, choices=ORDER_STATUS)