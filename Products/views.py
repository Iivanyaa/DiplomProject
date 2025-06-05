from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import (extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes,
                                    OpenApiExample, inline_serializer, OpenApiResponse)
from Orders.models import Order, OrderProduct
from Users.models import MarketUser
from Users.serializers import UserSerializer, ViewUsernameSerializer
from .serializers import *
from .models import Product, Category, Cart, CartProduct, Parameters
from rest_framework import status, serializers
from django.core.mail import send_mail
import os
from .schema import *

# Документация для ProductsView
@products_list_schema
class ProductsView(APIView):
    # вьюшка для просмотра всех продуктов, либо если введены id, name или категория
    
    def get(self, request):
        """
        GET-запрос на просмотр продуктов.

        Параметры:
        id (int): идентификатор продукта
        name (str): название продукта
        categories (list): список идентификаторов категорий

        Возвращает:
        Response: объект ответа с сообщением об успешном поиске
            продуктов, если такие продукты существуют, или сообщение
            об ошибке, если продукты не найдены.
        """
        
        serializer = ProductSearchSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # если не переданы данные, выводим список всех продуктов
        if not any([key in serializer.validated_data for key in ['id', 'name', 'categories']]):
            products = Product.objects.all()

            return Response({'message': 'Все продукты',

                             'products': ProductsListSerializer(products, many=True).data
                             }, status=status.HTTP_200_OK)
        
        # если передана категория, выводим список продуктов в этой категории
        if 'categories' in serializer.validated_data:
            products = Product.objects.filter(categories__in=serializer.validated_data['categories'])
            return Response({'message': 'Продукты в категории',
                             'products': ProductsListSerializer(products, many=True).data
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
        """
        POST-запрос на создание продукта.

        Параметры:
        request (Request): объект запроса Django
        perm (str): права, необходимые для создания продукта (по умолчанию 'Users.add_product')

        Возвращает:
        Response: объект ответа с сообщением об успешном создании
            продукта, если такие права есть, или сообщение
            об ошибке, если таких прав нет.
        """
        serializer = ProductSerializer(data=request.data)
        print(serializer.is_valid())
        if not serializer.is_valid:
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        if not MarketUser.AccessCheck(self, request, perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_401_UNAUTHORIZED)
                
        # создаем продукт
        product = Product.objects.create(
            name=serializer.validated_data['name'],
            price=serializer.validated_data['price'],
            description=serializer.validated_data['description'],
            quantity=serializer.validated_data['quantity'],
            seller=MarketUser.objects.get(id=request.session.get('user_id'))
        )

        # Добавляем категории (если они указаны)
        if 'categories' in serializer.validated_data:
            categories = serializer.validated_data['categories']
            for category in categories:
                product.categories.add(category)

        # привязываем продукт к пользователю
        # seller = MarketUser.objects.get(id=request.session.get('user_id'))
        # seller.priducts.add(product)
        #product.seller.add(MarketUser.objects.get(id=request.session.get('user_id')))

        return Response({
            'message': 'Продукт успешно создан',
            'id': product.id,
            'name': product.name,
            'categories': [c.name for c in product.categories.all()]
        }, status=status.HTTP_201_CREATED)
    # вьюшка для изменения продукта
    def put(self, request):
        """
        PUT-запрос на изменение продукта.

        Параметры:
        request (Request): объект запроса Django

        Возвращает:
        Response: объект ответа с сообщением об успешном изменении
            продукта, если такие права есть, или сообщение
            об ошибке, если таких прав нет.
        """
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
        try:
            product = Product.objects.get(pk=serializer.validated_data['id'])
        # если продукт не найден, возвращаем ошибку
        except Product.DoesNotExist:
            return Response({'message': 'Продукт не найден'}, status=status.HTTP_404_NOT_FOUND)
        # проверяем, что продукт с таким названием не существует
        if 'name' in serializer.validated_data.keys(): 
            if Product.objects.filter(name=serializer.validated_data['name']).exists():
                return Response({'message': 'Продукт с таким названием уже существует'}, status=status.HTTP_400_BAD_REQUEST)
        # изменяем только разрешенные поля
        allowed_fields = ['price', 'description', 'quantity', 'is_available', 'name']
        update_data = {k: v for k, v in serializer.validated_data.items() if k in allowed_fields}
        for key, value in update_data.items():
            setattr(product, key, value)
            
        product.save()
        # если изменена цена, то уведомляем админов
        if 'price' in update_data:
            for user in MarketUser.objects.filter(user_type='Admin'):
                user.email_user('Цена продукта изменена', f"Цена продукта {product.name} была изменена на {product.price}")

        return Response(
            {"message": "Продукт успешно изменен",
             "product": ProductSerializer(product).data
             }, status=status.HTTP_200_OK)
    # вьюшка для удаления продукта
    def delete(self, request, perm='Users.delete_product'):
        """
        DELETE-запрос на удаление продукта.

        Параметры:
        request (Request): объект запроса Django
        perm (str): права, необходимые для удаления продукта (по умолчанию 'Users.delete_product')

        Возвращает:
        Response: объект ответа с сообщением об успешном удалении
            продукта, если такие права есть, или сообщение
            об ошибке, если таких прав нет.
        """
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
    
    # вьюшка для добавления продукта в корзину
    def patch(self, request, perm='Users.add_to_cart'):
        """
        PATCH-запрос на добавление продукта в корзину.

        Параметры:
        request (Request): объект запроса Django
        perm (str): права, необходимые для добавления продукта в корзину (по умолчанию 'Users.add_to_cart')

        Возвращает:
        Response: объект ответа с сообщением об успешном добавлении
            продукта в корзину, если такие права есть, или сообщение
            об ошибке, если таких прав нет.
        """

        serializer = ProductAddToCartSerializer(data=request.data)
        
        # проверяем валидность данных
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                            
        # проверяем наличие прав пользователя
        if not MarketUser.AccessCheck(self, request, perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)

        # ищем продукт по id или названию
        try:
            product = Product.objects.get(id=serializer.validated_data['id'])
        # если продукт не найден, возвращаем ошибку
        except Product.DoesNotExist:
            return Response({'message': 'Продукт не найден'}, status=status.HTTP_404_NOT_FOUND)

        # проверяем наличие необходимого количества товара
        if product.quantity < serializer.validated_data['quantity']:
            return Response({'message': 'Недостаточное количество товара'}, status=status.HTTP_400_BAD_REQUEST)
        # проверяем доступность продукта
        if not product.is_available:
            return Response({'message': 'Продукт недоступен для заказа'}, status=status.HTTP_400_BAD_REQUEST)
        # получаем текущего пользователя
        user = MarketUser.objects.get(id=request.session.get('user_id'))
        
        # Получаем активную корзину пользователя (или создаем новую)
        cart, created = Cart.objects.get_or_create(user=user)

        # Создаем или обновляем CartProduct
        cart_product, created = CartProduct.objects.get_or_create(
        product=product,
        cart=cart,
        defaults={'quantity': serializer.validated_data['quantity']}
        )

        if not created:
            cart_product.quantity = serializer.validated_data['quantity']
            cart_product.save()

        return Response({
            'message': 'Продукт добавлен в корзину',
            'cart_id': cart.id,
            'product_id': product.id,
            'quantity': cart_product.quantity
        }, status=status.HTTP_200_OK)


# вьюшка для изменения продавцом доступности товаров
@products_change_schema
class ProductsChangeView(APIView):
    # вьюшка для изменения продавцом доступности товаров
    def put(self, request, perm='Users.change_product_availability'):
        serializer = ProductChangeAvailabilitySerializer(data=request.data)
        # проверяем имеет ли пользователь право на изменение доступности продуктов
        if not MarketUser.AccessCheck(self, request, perm):
            print('проверку прав на изменение доступности продуктов не прошли')
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        print('проверку прав на изменение доступности продуктов прошли')
        print(serializer.is_valid())
        # если id продукта не передан, то меняем is_available всех продуктов продавца
        if 'id' not in serializer.validated_data:
            print('id нет в данных, меняем is_available всех продуктов продавца')
            Product.objects.filter(seller=request.user).update(is_available=request.data['is_available'])
            return Response({'message': 'Доступность продуктов успешно изменена'}, status=status.HTTP_200_OK)
        # если id продукта передан, то меняем is_available конкретного продукта
        print('id есть в данных, меняем is_available конкретного продукта')
        product = Product.objects.get(id=request.data['id'])
        product.is_available = request.data['is_available']
        product.save()
        return Response({'message': 'Доступность продукта успешно изменена'}, status=status.HTTP_200_OK)

    # вьюшка для добавления параметров товару
    def post(self, request, perm='Users.add_product_parameters'):
        serializer = CreateParametersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # проверяем имеет ли пользователь право на добавление параметров продуктов
        if not MarketUser.AccessCheck(self, request, perm):
            print('проверку прав на добавление параметров продуктов не прошли')
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        print('проверку прав на добавление параметров продуктов прошли')
        # если id продукта не передан, то возвращаем ошибку
        if 'product_id' not in serializer.validated_data:
            print('id продукта не передан')
            return Response({'message': 'ID продукта не передан'}, status=status.HTTP_400_BAD_REQUEST)
        print('id есть в данных, добавляем параметры конкретного продукта')
        # проверяем, что продукт относится к продавцу
        if serializer.validated_data['product_id'] not in Product.objects.filter(seller=request.user).values_list('id', flat=True):
            print('продукт относится к другому продавцу')
            return Response({'message': 'Продукт относится к другому продавцу'}, status=status.HTTP_400_BAD_REQUEST)
        print('все проверки прошли, добавляем параметры конкретного продукта')
        print(serializer.validated_data)
        # если id продукта передан, то добавляем параметры конкретного продукта
        Product.objects.get(id=serializer.validated_data['product_id']).parameters.add(
            Parameters.objects.create(
                product=Product.objects.get(id=serializer.validated_data['product_id']),
                name=serializer.validated_data['name'],
                value=serializer.validated_data.get('value')
            )
        )
        return Response({'message': 'Параметры продукта успешно добавлены'}, status=status.HTTP_200_OK)

        #вьюшка для удаления параметров товара
    def delete(self, request, perm='Users.delete_product_parameters'):
        serializer = DeleteParametersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # проверяем имеет ли пользователь право на удаление параметров продуктов
        if not MarketUser.AccessCheck(self, request, perm):
            print('проверку прав на удаление параметров продуктов не прошли')
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # если id параметра не передан, то удаляем все параметры продукта
        if 'parameters_id' not in serializer.validated_data:
            Product.objects.get(id=serializer.validated_data['product_id']).parameters.clear()
            return Response({'message': 'Параметры продукта успешно удалены'}, status=status.HTTP_200_OK)   
        # проверяем, что продукт относится к продавцу
        if serializer.validated_data['product_id'] not in Product.objects.filter(seller=request.user).values_list('id', flat=True):
            return Response({'message': 'Продукт относится к другому продавцу'}, status=status.HTTP_400_BAD_REQUEST)
        # если id параметра передан, то пробуем его получить
        try:
            Parameters.objects.get(id=serializer.validated_data['parameters_id'])
        except Parameters.DoesNotExist:
            return Response({'message': 'Такого параметра не существует'}, status=status.HTTP_404_NOT_FOUND)
        # параметры существуют, удаляем    
        Product.objects.get(id=serializer.validated_data['product_id']).parameters.get(id=serializer.validated_data['parameters_id']).delete()
        return Response({'message': 'Параметры продукта успешно удалены'}, status=status.HTTP_200_OK)

    # вьюшка для изменения параметров товара
    def patch(self, request, perm='Users.update_product_parameters'):
        serializer = UpdateParametersSerializer(data=request.data)
        print('проверяем сериализатор')
        print(serializer.is_valid())
        serializer.is_valid(raise_exception=True)
        print('проверку прав на изменение параметров продуктов прошли')
        # проверяем имеет ли пользователь право на изменение параметров продуктов
        if not MarketUser.AccessCheck(self, request, perm):
            print('проверку прав на изменение параметров продуктов не прошли')
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # если id продукта не передан, то возвращаем ошибку
        if 'product_id' not in serializer.validated_data:
            print('id продукта не передан')
            return Response({'message': 'ID продукта не передан'}, status=status.HTTP_400_BAD_REQUEST)
        # проверяем, что продукт относится к продавцу
        if serializer.validated_data['product_id'] not in Product.objects.filter(seller=request.user).values_list('id', flat=True):
            print('продукт относится к другому продавцу')
            return Response({'message': 'Продукт относится к другому продавцу'}, status=status.HTTP_400_BAD_REQUEST)
        # если id продукта передан, то изменяем параметры конкретного продукта
        print('id есть в данных, меняем параметры конкретного продукта')
        try:
            Parameters.objects.get(id=serializer.validated_data['parameters_id'])
        except Parameters.DoesNotExist:
            return Response({'message': 'Такого параметра не существует'}, status=status.HTTP_404_NOT_FOUND)
        param =Product.objects.get(id=serializer.validated_data['product_id']).parameters.all()
        print(param.all())
        param.update(
            name=serializer.validated_data['name'],
            value=serializer.validated_data['value']
        )
        return Response({'message': 'Параметры продукта успешно изменены'}, status=status.HTTP_200_OK)


# Документация для CategoriesView
@categories_view_schema
class CategoriesView(APIView):
    # создание категории
    def post(self, request, perm='Users.create_category'):
        """
        POST-запрос на создание категории.

        Параметры:
        request (Request): объект запроса Django
        perm (str): права, необходимые для создания категории (по умолчанию 'Users.create_category')

        Возвращает:
        Response: объект ответа с сообщением об успешном создании
            категории, если такие права есть, или сообщение
            об ошибке, если таких прав нет.
        """
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
        """
        DELETE-запрос на удаление категории.

        Параметры:
        request (Request): объект запроса Django
        perm (str): права, необходимые для удаления категории (по умолчанию 'Users.delete_category')

        Возвращает:
        Response: объект ответа с сообщением об успешном удалении
            категории, если такие права есть, или сообщение
            об ошибке, если таких прав нет.
        """
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
        """
        PUT-запрос на изменение категории.

        Параметры:
        request (Request): объект запроса Django
        perm (str): права, необходимые для изменения категории (по умолчанию 'Users.update_category')

        Возвращает:
        Response: объект ответа с сообщением об успешном изменении
            категории, если такие права есть, или сообщение
            об ошибке, если таких прав нет.
        """
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
        """
        Вьюшка для получения категории по id или имени, либо получения всех категорий,
        если id или имя не указаны.

        Параметры:
        request (Request): объект запроса Django
        perm (str): разрешение, необходимое для получения категории

        Возвращает:
        Response: объект ответа с данными категории, если категория найдена,
            или сообщение об ошибке, если категория не найдена
        """
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


# Документация для CartView
@cart_view_schema
class CartView(APIView):
    # вьюшка для получения корзины
    def get(self, request, perm='Users.view_cart'):
        """
        Получить корзину пользователя.

        Параметры:
        request (Request): объект запроса Django
        perm (str): требуемое разрешение для получения корзины

        Возвращает:
        Response: объект ответа с данными корзины, если пользователь имеет
            необходимые права, или сообщение об ошибке, если пользователь не
            имеет необходимых прав.
        """
        # проверяем имеет ли пользователь право на получение корзины
        if not MarketUser.AccessCheck(self, request, perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # получаем текущего пользователя
        user = MarketUser.objects.get(id=request.session.get('user_id'))
        # Получаем активную корзину пользователя (или создаем новую)
        cart, created = Cart.objects.get_or_create(user=user)
        # Получаем стоимость корзины
        total_price = int(cart.TotalPrice())
        # возвращаем корзину
        return Response({
            'message': 'Корзина успешно получена',
            'id': cart.id,
            'Cart_products': [
                {
                    'name': product.name,
                    'quantity': product.cart_products.get(cart=cart).quantity,
                    'price': product.price,
                    'id': product.id,
                    'is_available': product.is_available,
                    'seller': product.seller.username
                }
                for product in cart.products.all()
            ],
            'Total_price': total_price
        }, status=status.HTTP_200_OK)
    # вьюшка для удаления продукта из корзины
    def delete(self, request, perm='Users.delete_product_from_cart'):
        """
        Удаляет продукт из корзины пользователя.

        """
        serializer = CartProductSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # проверяем имеет ли пользователь право на удаление товаров из корзины
        if not MarketUser.AccessCheck(self, request, perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # ищем товар по id или названию
        products = Product.objects.filter(**serializer.validated_data)
        # если товар не найдена, возвращаем ошибку
        if not products.exists():
            return Response({'message': 'Товар не найдена'}, status=status.HTTP_404_NOT_FOUND)
        # ищем корзину текущего пользователя
        user = MarketUser.objects.get(id=request.session.get('user_id'))
        cart, created = Cart.objects.get_or_create(user=user)
        # если товар есть в корзине, то удаляем его из корзины
        if products.first() in cart.products.all():
            cart_product = CartProduct.objects.filter(cart=cart, product=products.first()).delete()
            return Response({"message": "Товар успешно удален из корзины"}, status=status.HTTP_200_OK)
        # если товара нет в корзине, то возвращаем ошибку
        return Response({"message": "Товар не находится в корзине"}, status=status.HTTP_400_BAD_REQUEST)

    # вьюшка для обновления продукта в корзине
    def put(self, request, perm='Users.update_product_in_cart'):
        """
        Обновляет продукт в корзине пользователя.

        Параметры:
        serializer (ProductAddToCartSerializer): сериализатор данных запроса

        Возвращает:
        Response: объект ответа с сообщением об успешном обновлении товара в
            корзине, если пользователь имеет необходимые права и товар
            находится в корзине, или сообщение об ошибке, если товар не
            найден или нет прав на обновление.
        """
        serializer = ProductAddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # проверяем имеет ли пользователь право на обновление товаров в корзине
        if not MarketUser.AccessCheck(self, request, perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # ищем товар по id или названию
        products = Product.objects.get(id=serializer.validated_data['id'])
        # если товар не найдена, возвращаем ошибку
        if products is None:
            return Response({'message': 'Товар не найден'}, status=status.HTTP_404_NOT_FOUND)
        # ищем корзину текущего пользователя
        user = MarketUser.objects.get(id=request.session.get('user_id'))
        cart, created = Cart.objects.get_or_create(user=user)
        # проверяем достаточное количество товара в наличии у продавца
        if products.quantity < serializer.validated_data['quantity']:
            return Response({'message': 'Недостаточное количество товара'}, status=status.HTTP_400_BAD_REQUEST)
        # проверяем доступность продукта
        if not products.is_available:
            return Response({'message': 'Товар недоступен для заказа'}, status=status.HTTP_400_BAD_REQUEST)
        # если товар есть в корзине, то обновляем количество товара в корзине
        if products in cart.products.all():
            cart_product = CartProduct.objects.filter(cart=cart, product=products).update(quantity=serializer.validated_data['quantity'])
            return Response({"message": "Товар успешно обновлен в корзине"}, status=status.HTTP_200_OK)
        # если товара нет в корзине, то возвращаем ошибку
        return Response({"message": "Товар не находится в корзине"}, status=status.HTTP_400_BAD_REQUEST)

    # вьюшка для оформления заказа
    def post(self, request, perm='Users.order'):
        """
        Оформляет заказ.

        Параметры:
        request (Request): объект запроса Django

        Возвращает:
        Response: объект ответа с сообщением об успешном оформлении заказа,
            если пользователь имеет необходимые права, или сообщение об ошибке,
            если пользователь не имеет необходимых прав.
        """
        # проверяем имеет ли пользователь право на оформление заказа
        if not MarketUser.AccessCheck(self, request, perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # получаем текущего пользователя
        user = MarketUser.objects.get(id=request.session.get('user_id'))
        # Получаем активную корзину пользователя (или создаем новую)
        cart, created = Cart.objects.get_or_create(user=user)
        # проверяем, есть ли в корщине товары
        if not cart.cart_products.exists():
             return Response({'message': 'В корзине нет товаров'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        # проверяем, есть ли у покупателя контакты
        if not user.contacts.exists():
            return Response({'message': 'Необходимо добавить контактную информацию для оформления заказа'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        # проверяем достаточное количество товара в наличии у продавца
        for product in cart.cart_products.all():
            if product.product.quantity < product.quantity:
                return Response({'message': 'Недостаточное количество товара',
                                 'id': product.product.id,
                                 'name': product.product.name},
                                  status=status.HTTP_406_NOT_ACCEPTABLE)
        # проверяем доступность продукта
        for product in cart.cart_products.all():
            if not product.product.is_available:
                return Response({'message': 'Товар недоступен для заказа',
                                 'id': product.product.id,
                                 'name': product.product.name},
                                  status=status.HTTP_406_NOT_ACCEPTABLE)
        # Создаем заказ
        order = Order.objects.create(
            user=user,
            total_price=cart.TotalPrice()
        )
        # добавляем товары из корзины в заказ
        for product in cart.cart_products.all():
            order_product = OrderProduct.objects.create(
                order=order,
                product=product.product,
                quantity=product.quantity,
                seller=product.product.seller,
                buyer=product.cart.user,
                status='new'
            )
            order.order_products.add(order_product)
            # уменьшаем количество товара в БД
            product.product.quantity -= product.quantity
            product.product.save()
            # удаляем товар из корзины
            cart_product = CartProduct.objects.filter(cart=cart, product=product.product).delete()
        # очищаем корзину
        cart.products.all().delete()
        # отправляем email
        send_mail(
            subject='Новый заказ',
            message=f'Вы успешно оформили новый заказ:{order}',
            recipient_list=[user.email],
            from_email=os.getenv('EMAIL_HOST_USER'),
            fail_silently=True
        )
        return Response({"message": "Заказ успешно оформлен",
                         "id": order.id,
                         "total_price": order.total_price,
                         "order_products": [order_product.product.name for order_product in order.order_products.all()]
                         }, status=status.HTTP_201_CREATED)

