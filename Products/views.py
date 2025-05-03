from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from Users.models import MarketUser
from .serializers import ProductSearchSerializer, ProductSerializer
from .models import Product
from rest_framework import status


# вьюшка для обработки запросов к продуктам
class ProductsView(APIView):
    # вьюшка для поиска продукта
    def get(self, request):
        serializer = ProductSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # ищем продукт по id или названию
        products = Product.objects.filter(**serializer.validated_data)
        if not products.exists():
            return Response({'message': 'Продукт не найден'}, status=status.HTTP_404_NOT_FOUND)
        # если продукт найден, возвращаем его
        product = products.first()
        return Response({'message': 'Продукт найден', 'id': product.id, 'name': product.name}, status=status.HTTP_200_OK)
    # вьюшка для создания продукта
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # Получаем текущего пользователя из сессии
        user_id = request.session.get('user_id')
        if not user_id:
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
        # Получаем объект пользователя по ID
        user = MarketUser.objects.get(id=user_id)
        # Проверяем, имеет ли пользователь право на создание продукта
        if not user.has_perm('Users.add_product'):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # проверяем, что продукт с таким названием не существует
        if Product.objects.filter(name=serializer.validated_data['name']).exists():
            return Response({'message': 'Продукт с таким названием уже существует'}, status=status.HTTP_400_BAD_REQUEST)
        # создаем продукт
        product = Product.objects.create(**serializer.validated_data)
        return Response({
                         'message': 'Продукт успешно создан',
                         'id': product.id,
                         'name': product.name,
                         'price': product.price,
                         'description': product.description,
                         'quantity': product.quantity,
                         'is_available': product.is_available
                         }
                         , status=status.HTTP_201_CREATED)
    # вьюшка для изменения продукта
    def put(self, request):
        serializer = ProductSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # Получаем текущего пользователя из сессии
        user_id = request.session.get('user_id')
        if not user_id:
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
        # Получаем объект пользователя по ID
        user = MarketUser.objects.get(id=user_id)
        # Проверяем, имеет ли пользователь право на удаление продукта
        if not user.has_perm('Users.delete_product'):
            print(user)
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # Ищем продукт
        
        # проверяем, что продукт с таким названием не существует
        if Product.objects.filter(name=serializer.validated_data['name']).exists():
            return Response({'message': 'Продукт с таким названием уже существует'}, status=status.HTTP_400_BAD_REQUEST)
        # изменяем продукт
        product = Product.objects.filter(pk=serializer.validated_data['id']).update(**serializer.validated_data)
        return Response(product, message='Продукт успешно изменен', status=status.HTTP_200_OK)
    # вьюшка для удаления продукта
    def delete(self, request):
        serializer = ProductSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # Получаем текущего пользователя из сессии
        user_id = request.session.get('user_id')
        if not user_id:
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
        # Получаем объект пользователя по ID
        user = MarketUser.objects.get(id=user_id)
        # Проверяем, имеет ли пользователь право на удаление продукта
        if not user.has_perm('Users.delete_product'):
            print(user)
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # ищем продукт по id или названию
        products = Product.objects.filter(**serializer.validated_data)
        # если продукт не найден, возвращаем ошибку
        if not products.exists():
            return Response({'message': 'Продукт не найден'}, status=status.HTTP_404_NOT_FOUND)
        product = Product.objects.filter(**serializer.validated_data).delete()
        return Response({"message":"Продукт успешно удален"}, status=status.HTTP_200_OK)
    

