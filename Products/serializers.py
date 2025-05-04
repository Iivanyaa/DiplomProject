from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Product, Category

# сериализаторы для продуктов
class ProductSerializer(serializers.ModelSerializer):
    categories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.all(),
        required=False
    )
    
    class Meta:
        model = Product
        fields = ['name', 'price', 'description', 'quantity', 'is_available', 'parameters', 'categories']


# сериалазатор для поиска продуктов
class ProductSearchSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_blank=True)
    categories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.all(),
        required=False
    )

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
        if len([key for key, value in attrs.items() if value is not None]) > 1:
            raise ValidationError('Укажите только один параметр')

        return attrs
    
class ProductUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    price = serializers.DecimalField(required=False, allow_null=True, max_digits=10, decimal_places=2)
    description = serializers.CharField(required=False, allow_blank=True)
    quantity = serializers.IntegerField(required=False, allow_null=True)
    is_available = serializers.BooleanField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_blank=True)
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
        # Проверяем, что передано поле id
        if not attrs.get('id'):
            raise ValidationError("Укажите id для обновления.")
        return attrs


class CategorySerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(required=True, allow_blank=False)

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
        return attrs

class CategorySearchSerializer(CategorySerializer):
    id = serializers.IntegerField(required=False, allow_null=True)


class CategoryGetSerializer(CategorySerializer):
    id = serializers.IntegerField(required=False, allow_null=False)
    name = serializers.CharField(required=False, allow_null=True)


class CategoryUpdateSerializer(CategorySerializer):
    id = serializers.IntegerField(required=True, allow_null=False)
    name = serializers.CharField(required=False, allow_null=True)
