from rest_framework import serializers
from .models import User, Buyer
from django.contrib.auth.hashers import make_password


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [                                                           'username', 'password', 'email']

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().update(instance, validated_data)

class BuyerRegSerializer(UserSerializer):
    class Meta:
        model = Buyer
        fields = ['email', 'password', 'username', 'first_name', 'last_name', 'phone_number']


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
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError("New password cannot be the same as old password.")
        return attrs
    

# Сериализатор для удаления пользователя
class DeleteUserSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)  # Идентификатор пользователя (обязательное поле)

    def validate(self, attrs):
        # Проверяем, существует ли пользователь с данным идентификатором
        if not User.objects.filter(id=attrs['user_id']).exists():
            raise serializers.ValidationError("Пользователь не существует.")  # Выбрасываем ошибку, если пользователь не найден
        return attrs
    

class DeleteUserDataSerializer(serializers.Serializer):
    data_to_delete = serializers.ListField(child=serializers.CharField(), required=True)  # Список данных для удаления
   
    





# class SellerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Seller
#         fields = ['company_name', 'company_address', 'EMAIL', 'Available_products', 'password']