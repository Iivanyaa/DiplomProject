from django.forms import ValidationError
from rest_framework import serializers
from .models import MarketUser, Contact, UserGroup
from django.contrib.auth.hashers import make_password



class UserSerializer(serializers.ModelSerializer):
    # Добавляем поле user_type, которое используется только для записи,
    # но не является частью модели MarketUser
    user_type = serializers.CharField(write_only=True, required=False, default='Buyer')

    class Meta:
        model = MarketUser
        # Явно указываем поля, которые используем
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'user_type', 'phone_number']
        extra_kwargs = {
            # 'password' должно быть только для записи (не отдается в ответе)
            'password': {'write_only': True},
            # 'id' должно быть только для чтения (не принимается в запросе)
            'id': {'read_only': True}
        }

    # DRF автоматически вызовет этот метод для валидации поля 'email'
    def validate_email(self, value):
        if MarketUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с такой почтой уже существует.")
        return value

    # DRF автоматически вызовет этот метод для валидации поля 'username'
    def validate_username(self, value):
        if MarketUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким логином уже существует.")
        return value

    def create(self, validated_data):
        """
        Переопределяем метод создания, чтобы корректно обработать
        создание пользователя и добавление его в группу.
        """
        # Извлекаем user_type, он нам не нужен для создания MarketUser
        user_type_name = validated_data.pop('user_type', 'Buyer')

        # Используем create_user для правильного хеширования пароля
        user = MarketUser.objects.create_user(**validated_data)

        # Добавляем пользователя в группу
        try:
            group = UserGroup.objects.get(name=user_type_name)
            group.user_set.add(user)
        except UserGroup.DoesNotExist:
            # Эту ошибку стоит логировать, т.к. это проблема конфигурации сервера
            print(f"Внимание: Группа '{user_type_name}' не найдена.")
            pass

        return user

# class UserRegSerializer(UserSerializer):
#     class Meta:
#         model = MarketUser
#         fields = ['user_type', 'email', 'password', 'username', 'first_name', 'last_name', 'phone_number']
#         write_only_fields = ('password')

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
        if not attrs.get('old_password') or not attrs.get('new_password'):
            raise ValidationError("Укажите old_password и new_password.")
        if attrs.get('old_password') == attrs.get('new_password'):
            raise ValidationError("Новый пароль должен отличаться от старого.")
        return attrs

    

# Сериализатор для удаления пользователя
class DeleteUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    username = serializers.CharField(required=False, allow_null=True)


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
class GetUserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketUser
        id = serializers.IntegerField(required=False, allow_null=True)
        fields = ['id']
    
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

#Сериализатор для восстановления пароля
class RestorePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    

class ViewUsernameSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketUser
        fields = ['username']


class AddContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'phone']

class UpdateContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'phone']
        extra_kwargs = {
            'id': {'required': False, 'allow_null': True},
            'city': {'required': False, 'allow_null': True},
            'street': {'required': False, 'allow_null': True},
            'house': {'required': False, 'allow_null': True},
            'structure': {'required': False, 'allow_null': True},
            'building': {'required': False, 'allow_null': True},
            'apartment': {'required': False, 'allow_null': True},
            'phone': {'required': False, 'allow_null': True},
        }

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

class DeleteContactSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True, allow_null=True)

class GetContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id']
        extra_kwargs = {
            'id': {'required': False, 'allow_null': True},
        }


class SocialAuthSerializer(serializers.Serializer):
    """
    Сериализатор для аутентификации через социальные сети.
    Ожидает название бэкенда (например, 'vk-oauth2', 'google-oauth2')
    и код авторизации, полученный от социальной сети.
    """
    backend = serializers.CharField(max_length=50, help_text="Название бэкенда социальной сети (например, 'vk-oauth2', 'google-oauth2').")
    code = serializers.CharField(help_text="Код авторизации, полученный от социальной сети.")

    # Можно добавить валидацию для backend, чтобы убедиться, что он из списка разрешенных
    def validate_backend(self, value):
        allowed_backends = ['vk-oauth2', 'google-oauth2'] # Добавь другие, если нужны
        if value not in allowed_backends:
            raise serializers.ValidationError(f"Неизвестный или неподдерживаемый бэкенд: {value}. Разрешены: {', '.join(allowed_backends)}")
        return value


class AvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketUser
        fields = ('avatar',)




__all__ = [
    'UserSerializer',
    # 'UserRegSerializer',
    'GetUserDataSerializer',
    'DeleteUserDataSerializer',
    'RestorePasswordSerializer',
    'ViewUsernameSerializer',
    'AddContactSerializer',
    'UserUpdateSerializer',
    'LoginSerializer',
    'ChangePasswordSerializer',
    'DeleteUserSerializer',
    'UpdateContactSerializer',
    'DeleteContactSerializer',
    'GetContactSerializer',
    'SocialAuthSerializer',
    'AvatarSerializer'
]

# class SellerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Seller
#         fields = ['company_name', 'company_address', 'EMAIL', 'Available_products', 'password']