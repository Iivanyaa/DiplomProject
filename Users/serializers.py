from django.forms import ValidationError
from rest_framework import serializers
from .models import MarketUser
from django.contrib.auth.hashers import make_password


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketUser
        fields = ['username', 'password', 'email']

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().update(instance, validated_data)

class UserRegSerializer(UserSerializer):
    class Meta:
        model = MarketUser
        fields = ['user_type', 'email', 'password', 'username', 'first_name', 'last_name', 'phone_number']


class UserUpdateSerializer(UserSerializer):
    class Meta:
        model = MarketUser
        username = serializers.CharField(required=False, allow_null=True)
        fields = ['id', 'user_type', 'email','first_name', 'last_name', 'phone_number']

    def validate(self, attrs):
            # Проверяем, существует ли пользователь с данным идентификатором
        # if not MarketUser.objects.filter(id=attrs['id']).exists():
        #     raise serializers.ValidationError("Пользователь не существует.")  # Выбрасываем ошибку, если пользователь не найден
        
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
        
        attrs = super().validate(self.initial_data)
        # # Проверяем, что хотя бы одно поле передано
        # if not attrs.get('id') and not attrs.get('name'):
        #     raise ValidationError("Укажите id или name для поиска.")

        # Проверяем, что не передано более одного параметра
        
        return attrs

        return super().validate(attrs)

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if not username or not password:
            raise serializers.ValidationError("Username and password are required.")

        return attrs
    

# сериализатор смены пароля
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    

# Сериализатор для удаления пользователя
class DeleteUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    username = serializers.CharField(required=False, allow_null=True)  # Идентификатор пользователя (обязательное поле)

    def validate(self, attrs):
        # Проверяем, существует ли пользователь с данным идентификатором
        if not MarketUser.objects.filter(**attrs).exists():
            raise serializers.ValidationError("Пользователь не существует.")  # Выбрасываем ошибку, если пользователь не найден
        
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
        
        attrs = super().validate(self.initial_data)
        # # Проверяем, что хотя бы одно поле передано
        # if not attrs.get('id') and not attrs.get('name'):
        #     raise ValidationError("Укажите id или name для поиска.")

        # Проверяем, что не передано более одного параметра
        
        return attrs

    

# Сериализатор для получения данных пользователя по ID
class GetUserDataSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True) # Идентификатор пользователя (обязательное поле)
    
    def validate(self, attrs):
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
        
        attrs = super().validate(self.initial_data)
        
        return attrs
    

    

class DeleteUserDataSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    data_to_delete = serializers.ListField(
        child=serializers.CharField(),  # Список строковых значений
        required=True,  # Обязательное поле
        allow_null=False,  # Поле не может быть Null
        allow_empty=False  # не может быть пустым
    )
    # проверяем допустимость переданных данных
    def validate(self, attrs):
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
        
        attrs = super().validate(self.initial_data)
        
        return attrs

# Сериализатор для восстановления пароля
class RestorePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate(self, attrs):
        # Проверяем, существует ли пользователь с данным электронным адресом
        if not MarketUser.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("Пользователь с таким электронным адресом не найден.")
        return attrs
    

class ViewUsernameSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketUser
        fields = ['username']




# class SellerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Seller
#         fields = ['company_name', 'company_address', 'EMAIL', 'Available_products', 'password']