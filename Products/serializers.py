from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Product, Category, Cart, CartProduct, Parameters
from Users.models import MarketUser


class ParameterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Parameters.
    Используется для обработки вложенных параметров продукта.
    """
    class Meta:
        model = Parameters
        fields = ['name', 'value']

# сериализаторы для продуктов
class ProductSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Product.
    Используется для валидации и сохранения данных о продуктах.
    Также обрабатывает вложенные параметры и связь с продавцом и категориями.
    """
    # Вложенный сериализатор для параметров
    parameters = ParameterSerializer(many=True, required=False)
    
    # Поле для записи seller_id (Primary Key), доступно только для записи
    # seller_id = serializers.PrimaryKeyRelatedField(
    #     queryset=MarketUser.objects.all(), source='seller', write_only=True, required=False
    # )
    # Поле для чтения имени пользователя продавца, доступно только для чтения
    seller = serializers.CharField(source='seller.username', read_only=True)

    # Поле для категорий, принимающее список id
    categories = serializers.ListField(
        allow_empty=True,
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    # Поле для чтения названий категорий
    category_names = serializers.SerializerMethodField()
    
    # Сделаем поле description необязательным, так как оно может отсутствовать в YAML файле
    description = serializers.CharField(required=False)

    class Meta:
        model = Product
        fields = [
            'name', 'price', 'description', 'quantity', 'is_available',
            'created_at', 'updated_at', 'seller', 'parameters',
            'categories', 'category_names' # Добавлены поля для категорий
        ]
        # is_available и временные метки контролируются моделью или автоматически
        read_only_fields = ['created_at', 'updated_at', 'is_available', 'category_names'] 

    def get_category_names(self, obj):
        """
        Возвращает список названий категорий для продукта.
        """
        return [category.name for category in obj.categories.all()]

    def create(self, validated_data):
        """
        Создает новый продукт и связанные с ним параметры и категории.
        """
        parameters_data = validated_data.pop('parameters', [])
        category_names_data = validated_data.pop('categories', []) # Получаем названия категорий

        # Если описание отсутствует, установим его в пустую строку
        validated_data['description'] = validated_data.get('description', '')

        product = Product.objects.create(**validated_data)

        # Создание или связывание параметров
        for param_data in parameters_data:
            Parameters.objects.create(product=product, **param_data)

        # Создание или связывание категорий
        for category_name in category_names_data:
            category, created = Category.objects.get_or_create(name=category_name)
            product.categories.add(category) # Добавляем категорию к продукту

        return product

    def update(self, instance, validated_data):
        """
        Обновляет существующий продукт и его параметры и категории.
        """
        parameters_data = validated_data.pop('parameters', [])
        category_names_data = validated_data.pop('categories', []) # Получаем названия категорий

        # Обновление полей продукта
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save() # Метод save модели обновит is_available на основе quantity

        # Обновление или создание параметров:
        # Для простоты, мы удаляем все существующие параметры и создаем новые.
        # Для более сложной логики можно сравнивать существующие и обновлять/добавлять/удалять.
        instance.parameters.all().delete()
        for param_data in parameters_data:
            Parameters.objects.create(product=instance, **param_data)

        # Обновление категорий:
        # Удаляем все существующие категории и связываем заново
        instance.categories.clear() # Очищаем текущие категории
        for category_name in category_names_data:
            category, created = Category.objects.get_or_create(name=category_name)
            instance.categories.add(category) # Добавляем обновленные категории

        return instance


class ProductChangeAvailabilitySerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    is_available = serializers.BooleanField(required=True, allow_null=False)


class ProductsListSerializer(ProductSerializer):
    id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'description', 'quantity', 'is_available', 'parameters', 'categories']

# сериалазатор для поиска продуктов
class ProductSearchSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_blank=True)
    categories = serializers.CharField(
        required=False,
        allow_null=True
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
        # if len([key for key, value in attrs.items() if value is not None]) > 1:
        #     raise ValidationError('Укажите только один параметр')
        
        return attrs
    

class ProductAddToCartSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True, allow_null=False)
    quantity = serializers.IntegerField(required=True, allow_null=False)

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
    

class ProductAddSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, allow_blank=False)
    price = serializers.DecimalField(required=True, allow_null=False, max_digits=10, decimal_places=2)
    description = serializers.CharField(required=True, allow_blank=False)
    quantity = serializers.IntegerField(required=True, allow_null=False)
    is_available = serializers.BooleanField(required=True, allow_null=False)
    categories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.all(),
        required=True
    )


class ProductUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    price = serializers.DecimalField(required=False, allow_null=True, max_digits=10, decimal_places=2)
    description = serializers.CharField(required=False, allow_blank=True)
    quantity = serializers.IntegerField(required=False, allow_null=True)
    is_available = serializers.BooleanField(required=False, default=True)
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
    name = serializers.CharField(required=False, allow_blank=False)

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
        # проверка на вхождение хотябы 1 значения
        # if not attrs.get('id') and not attrs.get('name'):
        #     raise ValidationError("Укажите id или name для поиска.")
        return attrs

class CategorySearchSerializer(CategorySerializer):
    id = serializers.IntegerField(required=False, allow_null=True)


class CategoryGetSerializer(CategorySerializer):
    id = serializers.IntegerField(required=False, allow_null=False)
    name = serializers.CharField(required=False, allow_null=True)


class CategoryUpdateSerializer(CategorySerializer):
    id = serializers.IntegerField(required=True, allow_null=False)
    name = serializers.CharField(required=False, allow_null=True)


class CartProductSearchSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True, allow_null=False)


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


class CreateParametersSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True, allow_null=False)
    name = serializers.CharField(required=True, allow_null=False)
    value = serializers.CharField(required=False, allow_null=True)

class UpdateParametersSerializer(CreateParametersSerializer):
    parameters_id = serializers.IntegerField(required=True, allow_null=False)

class DeleteParametersSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True, allow_null=False)
    parameters_id = serializers.IntegerField(required=False, allow_null=True)

class ProductImportSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)

class ProductImportErrorSerializer(serializers.Serializer):
    message = serializers.CharField(required=True)
    errors = serializers.ListField(required=True)
    imported_count = serializers.IntegerField(required=True)
    updated_count = serializers.IntegerField(required=True)

class ProductImportSuccessSerializer(serializers.Serializer):
    imported_count = serializers.IntegerField(required=True)
    updated_count = serializers.IntegerField(required=True)


__all__ = [
    'ProductSerializer',
    'ProductSearchSerializer',
    'ProductAddToCartSerializer',
    'ProductUpdateSerializer',
    'CategorySerializer',
    'CategorySearchSerializer',
    'CategoryGetSerializer',
    'CategoryUpdateSerializer',
    'ProductAddSerializer',
    'ProductsListSerializer',
    'CartProductSearchSerializer',
    'ProductChangeAvailabilitySerializer',
    'CreateParametersSerializer',
    'UpdateParametersSerializer',
    'DeleteParametersSerializer',
    'ProductImportSerializer',
    'ParameterSerializer',
    'ProductImportSerializer',
    'ProductImportErrorSerializer',
    'ProductImportSuccessSerializer'
]