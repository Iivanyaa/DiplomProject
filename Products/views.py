from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from Users.models import MarketUser
from Users.serializers import UserSerializer, ViewUsernameSerializer
from .serializers import CategoryGetSerializer, CategoryUpdateSerializer, ProductSearchSerializer, ProductSerializer, ProductUpdateSerializer, CategorySerializer, CategorySearchSerializer
from .models import Product, Category
from rest_framework import status


# вьюшка для обработки запросов к продуктам
class ProductsView(APIView):
    # вьюшка для просмотра всех продуктов, либо если введены id, name или категория
    def get(self, request):
        serializer = ProductSearchSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # если не переданы данные, выводим список всех продуктов
        if not any([key in serializer.validated_data for key in ['id', 'name', 'categories']]):
            products = Product.objects.all()

            return Response({'message': 'Все продукты',
                             'products': ProductSerializer(products, many=True).data
                             }, status=status.HTTP_200_OK)
        
        # если передана категория, выводим список продуктов в этой категории
        if 'categories' in serializer.validated_data:
            products = Product.objects.filter(categories__in=serializer.validated_data['categories'])
            return Response({'message': 'Продукты в категории',
                             'products': ProductSerializer(products, many=True).data
                             }, status=status.HTTP_200_OK)
        
        # если категория не передана ищем продукт по id или названию
        products = Product.objects.filter(**serializer.validated_data)
        if not products.exists():
            return Response({'message': 'Продукт не найден'}, status=status.HTTP_404_NOT_FOUND)
        
        # если продукт найден, возвращаем его
        product = products.first()
        return Response({'message': 'Продукт найден',
                         'product': ProductSerializer(product).data
                         }, status=status.HTTP_200_OK)
    
    # вьюшка для создания продукта
    def post(self, request, perm='Users.add_product'):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not MarketUser.AccessCheck(self, request, perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
                
        # создаем продукт
        product = Product.objects.create(
            name=serializer.validated_data['name'],
            price=serializer.validated_data['price'],
            description=serializer.validated_data['description'],
            quantity=serializer.validated_data['quantity']
        )

        # Добавляем категории (если они указаны)
        if 'categories' in serializer.validated_data:
            categories = serializer.validated_data['categories']
            for category in categories:
                product.categories.add(category)

        # привязываем продукт к пользователю
        product.user.add(MarketUser.objects.get(id=request.session.get('user_id')))

        return Response({
            'message': 'Продукт успешно создан',
            'id': product.id,
            'name': product.name,
            'categories': [c.name for c in product.categories.all()]
        }, status=status.HTTP_201_CREATED)
    # вьюшка для изменения продукта
    def put(self, request):
        serializer = ProductUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # Получаем текущего пользователя из сессии
        user_id = request.session.get('user_id')
        if not user_id:
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
        # Получаем объект пользователя по ID
        user = MarketUser.objects.get(id=user_id)
        # Проверяем, имеет ли пользователь право на удаление продукта
        if not user.has_perm('Users.update_product'):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # Ищем продукт
        products = Product.objects.filter(pk=serializer.validated_data['id'])
        # если продукт не найден, возвращаем ошибку
        if not products.exists():
            return Response({'message': 'Продукт не найден'}, status=status.HTTP_404_NOT_FOUND)
        # проверяем, что продукт с таким названием не существует
        if 'name' in serializer.validated_data.keys(): 
            if Product.objects.filter(name=serializer.validated_data['name']).exists():
                return Response({'message': 'Продукт с таким названием уже существует'}, status=status.HTTP_400_BAD_REQUEST)
        # изменяем продукт
        product = Product.objects.filter(pk=serializer.validated_data['id']).update(**serializer.validated_data)
        new_product = Product.objects.get(pk=serializer.validated_data['id'])
        return Response(
            {"message": "Продукт успешно изменен",
             "product": {
                 "id": new_product.id,
                 "name": new_product.name,
                 "price": new_product.price,
                 "description": new_product.description,
                 "quantity": new_product.quantity,
                 "is_available": new_product.is_available
             }
             }, status=status.HTTP_200_OK)
    # вьюшка для удаления продукта
    def delete(self, request, perm='Users.delete_product'):
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
    

# вьюшка для обработки запросов к категориям
class CategoriesView(APIView):
    # создание категории
    def post(self, request, perm='Users.create_category'):
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # проверяем имеет ли пользователь право на создание категории
        if not MarketUser.AccessCheck(self, request, perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # проверяем нет ли категории с таким названием
        if 'name' in serializer.validated_data.keys(): 
            if Category.objects.filter(name=serializer.validated_data['name']).exists():
                return Response({'message': 'Категория с таким названием уже существует'}, status=status.HTTP_400_BAD_REQUEST)
        # создаем категорию
        category = Category.objects.create(**serializer.validated_data)
        return Response({'message': 'Категория успешно создана', **serializer.data}, status=status.HTTP_201_CREATED)
    # удаление категории
    def delete(self, request, perm='Users.delete_category'):
        serializer=CategorySearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # проверяем имеет ли пользователь право на удаление категории
        if not MarketUser.AccessCheck(self, request, perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # ищем категорию по id или названию
        categories = Category.objects.filter(**serializer.validated_data)
        # если категория не найдена, возвращаем ошибку
        if not categories.exists():
            return Response({'message': 'Категория не найдена'}, status=status.HTTP_404_NOT_FOUND)
        category = Category.objects.filter(**serializer.validated_data).delete()
        return Response({"message":"Категория успешно удалена"}, status=status.HTTP_200_OK)
    def put(self, request, perm='Users.update_category'):
        serializer=CategoryUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # проверяем имеет ли пользователь право на изменение категории
        if not MarketUser.AccessCheck(self, request, perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # ищем категорию по id или названию
        categories = Category.objects.filter(id=serializer.validated_data['id'])
        # если категория не найдена, возвращаем ошибку
        if not categories.exists():
            return Response({'message': 'Категория не найдена'}, status=status.HTTP_404_NOT_FOUND)
        # проверяем нет ли категории с таким названием
        if Category.objects.filter(name=serializer.validated_data['name']).exists():
            return Response({'message': 'Категория с таким названием уже существует'}, status=status.HTTP_400_BAD_REQUEST)
        # изменяем категорию
        category = Category.objects.filter(id=serializer.validated_data['id']).update(**serializer.validated_data)
        return Response(
            {"message": "Категория успешно изменена"}, status=status.HTTP_200_OK)
    # вьюшка для порлучения списка категорий либо категории по id или названию
    def get(self, request, perm='Users.get_category'):
        serializer = CategoryGetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # проверяем имеет ли пользователь право на получение категории
        if not MarketUser.AccessCheck(self, request, perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # проверяем переданы ли id и name
        if 'id' not in serializer.validated_data.keys() and 'name' not in serializer.validated_data.keys():
            # возвращаем все категории
            return Response({'message': 'Категории успешно получены', 'categories': CategorySerializer(Category.objects.all(), many=True).data}, status=status.HTTP_200_OK)
        # ищем категорию по id или названию
        categories = Category.objects.filter(**serializer.validated_data)
        # если категория не найдена, возвращаем ошибку
        if not categories.exists():
            return Response({'message': 'Категория не найдена'}, status=status.HTTP_404_NOT_FOUND)
        # если категория найдена, возвращаем ее
        category = categories.first()
        return Response({'message': 'Категория найдена', 'id': category.id, 'name': category.name}, status=status.HTTP_200_OK)
    
