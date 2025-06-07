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
import yaml
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly

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
        
        serializer = ProductSearchSerializer(data=request.query_params)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # если не переданы данные, выводим список всех продуктов
        if not any([key in serializer.validated_data for key in ['id', 'name', 'categories']]):
            products = Product.objects.all()

            return Response({'message': 'Все продукты',

                             'products': ProductsListSerializer(products, many=True).data
                             }, status=status.HTTP_200_OK)
        
        # если передан список категорий, выводим список продуктов в этих категориях
        if 'categories' in serializer.validated_data:
            queryset = Product.objects.prefetch_related('categories').all()

            # Получаем параметр 'categories' из URL
            categories_param = request.query_params.get('categories')

            if categories_param:
                # Параметр может быть как одним ID '1', так и несколькими '1,2,3'.
                # Разбиваем строку по запятым, чтобы получить список строк с ID.
                category_ids_str = categories_param.split(',')

                try:
                    # Преобразуем список строк с ID в список целых чисел.
                    # Это именно тот список, который ожидает фильтр '__in'.
                    category_ids = [int(cat_id) for cat_id in category_ids_str]
                except (ValueError, TypeError):
                    # Если преобразование не удалось, значит, входные данные некорректны (например, "abc")
                    return Response(
                        {"error": "Неверный формат ID категории. Пожалуйста, укажите ID в виде чисел, разделенных запятыми."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Фильтруем queryset, используя список целочисленных ID.
                # вызов .distinct() важен, чтобы избежать дублирования продуктов,
                # если один продукт принадлежит к нескольким запрошенным категориям.
                queryset = queryset.filter(categories__id__in=category_ids).distinct()

            # Сериализуем итоговый queryset и возвращаем ответ
            serializer = ProductSerializer(queryset, many=True)
            return Response(serializer.data)
        
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
        print(serializer.errors)
        print(serializer.validated_data)
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
                user.email_user('Цена продукта изменена', f"Цена продукта {product.name} была изменена на {product.price}",
                fail_silently=True)

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
            Product.objects.filter(seller=MarketUser.objects.get(id=request.session.get('user_id'))).update(is_available=request.data['is_available'])
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
        if serializer.validated_data['product_id'] not in Product.objects.filter(seller=MarketUser.objects.get(id=request.session.get('user_id'))).values_list('id', flat=True):
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
        if serializer.validated_data['product_id'] not in Product.objects.filter(seller=MarketUser.objects.get(id=request.session.get('user_id'))).values_list('id', flat=True):
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
        if serializer.validated_data['product_id'] not in Product.objects.filter(seller=MarketUser.objects.get(id=request.session.get('user_id'))).values_list('id', flat=True):
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

    # вьюшка для импорта товаров из xml файла продавца

@product_import_schema
class ProductImportView(APIView):
    """
    API-эндпоинт для импорта продуктов из файла YAML.

    Ожидает POST-запрос с файлом YAML, содержащим информацию о магазине,
    категориях и товарах, как в shop1.yaml.

    Пример YAML-файла (с учетом новой структуры, продавца, параметров и КАТЕГОРИЙ):
    shop: Связной
    categories:
      - id: 224
        name: Смартфоны
      - id: 5
        name: Телевизоры
    goods:
      - id: 4216292
        category: 224
        model: apple/iphone/xs-max
        name: Смартфон Apple iPhone XS Max 512GB (золотистый)
        price: 110000
        quantity: 14
        parameters:
          "Диагональ (дюйм)": 6.5
          "Разрешение (пикс)": 2688x1242
          "Встроенная память (Гб)": 512
          "Цвет": золотистый
      - id: 1234572
        category: 5
        model: samsung/qled-q90r
        name: Samsung QLED Q90R 65" 4K UHD Smart TV
        price: 2500
        quantity: 4
        parameters:
          "Screen Size (inches)": 65
          "Resolution (pixels)": 3840x2160
          "Smart TV": true
    """
    parser_classes = (MultiPartParser, FormParser) # Разрешает загрузку файлов

    def post(self, request, perm='Users.add_product'):
        """
        Обрабатывает POST-запрос для импорта продуктов.
        """
        # Проверяем, имеет ли пользователь право на импорт продуктов
        if not MarketUser.AccessCheck(self, request, perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # Проверяем, был ли загружен файл
        if 'file' not in request.FILES:
            return Response(
                {"error": "Файл YAML не был предоставлен. Пожалуйста, загрузите файл с именем 'file'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        yaml_file = request.FILES['file']

        # Проверяем расширение файла, чтобы убедиться, что это YAML
        if not yaml_file.name.endswith(('.yaml', '.yml')):
            return Response(
                {"error": "Неверный тип файла. Пожалуйста, загрузите файл .yaml или .yml."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Читаем содержимое файла
            file_content = yaml_file.read().decode('utf-8')
            # Загружаем данные из YAML
            full_data = yaml.safe_load(file_content)
        except yaml.YAMLError as e:
            return Response(
                {"error": f"Ошибка парсинга YAML-файла: {e}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Неизвестная ошибка при чтении файла: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if not isinstance(full_data, dict) or 'goods' not in full_data:
            return Response(
                {"error": "Ожидаемый формат YAML-файла: словарь с ключом 'goods', содержащим список продуктов."},
                status=status.HTTP_400_BAD_REQUEST
            )

        products_data = full_data.get('goods', [])
        categories_data = full_data.get('categories', [])

        if not isinstance(products_data, list):
            return Response(
                {"error": "Ключ 'goods' в YAML-файле должен содержать список продуктов."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Создаем карту ID категорий к их названиям
        category_id_to_name_map = {cat['id']: cat['name'] for cat in categories_data if 'id' in cat and 'name' in cat}

        imported_products_count = 0
        updated_products_count = 0
        errors = []

        # Получаем текущего аутентифицированного пользователя
        current_user = MarketUser.objects.get(id=request.session.get('user_id')) if MarketUser.AccessCheck(self, request, 'Users.add_product') else None
        
        # Обрабатываем каждый продукт в списке
        for item_data_raw in products_data:
            # Создаем копию для модификации без изменения исходных данных
            item_data = item_data_raw.copy()

            if not isinstance(item_data, dict):
                errors.append({"item": item_data_raw, "error": "Элемент списка 'goods' должен быть словарем."})
                continue

            # Определяем продавца для этого продукта
            seller_to_use = None
            if 'seller_id' in item_data: # Если seller_id указан в YAML
                try:
                    seller_to_use = MarketUser.objects.get(pk=item_data['seller_id'])
                except MarketUser.DoesNotExist:
                    errors.append({"item": item_data_raw, "error": f"Продавец с ID {item_data['seller_id']} не найден."})
                    continue
            elif current_user: # Если seller_id не указан, используем текущего аутентифицированного пользователя
                seller_to_use = current_user
            else:
                errors.append({"item": item_data_raw, "error": "Продавец не указан в YAML и пользователь не аутентифицирован."})
                continue

            # Добавляем seller_id в данные для сериализатора
            item_data['seller_id'] = seller_to_use.pk

            # Преобразование параметров: из словаря в список {'name': ..., 'value': ...}
            transformed_parameters = []
            if 'parameters' in item_data and isinstance(item_data['parameters'], dict):
                for param_name, param_value in item_data['parameters'].items():
                    transformed_parameters.append({'name': param_name, 'value': str(param_value)})
            item_data['parameters'] = transformed_parameters

            # Преобразование категорий: из ID в список названий
            transformed_categories = []
            if 'category' in item_data:
                category_id = item_data['category']
                category_name = category_id_to_name_map.get(category_id)
                if category_name:
                    transformed_categories.append(category_name)
                else:
                    errors.append({"item": item_data_raw, "error": f"Категория с ID {category_id} не найдена в верхнеуровневом списке категорий."})
                    # Продолжаем, чтобы не прерывать импорт из-за одной отсутствующей категории
            item_data['categories'] = transformed_categories
            
            # Удаляем поля, которые не соответствуют модели Product напрямую
            # (id, model, price_rrc, category) - они были обработаны или не нужны
            item_data.pop('id', None)
            item_data.pop('model', None)
            item_data.pop('price_rrc', None)
            item_data.pop('category', None) # Удаляем исходный ID категории


            # Попытка найти существующий продукт по 'name' и 'seller'
            existing_product = None
            if 'name' in item_data:
                try:
                    existing_product = Product.objects.get(name=item_data['name'], seller=seller_to_use)
                except Product.DoesNotExist:
                    pass
                except Product.MultipleObjectsReturned:
                    # Этого не должно произойти, если unique_together=('name', 'seller') установлено
                    errors.append({"item": item_data_raw, "error": f"Найдено несколько продуктов с именем '{item_data['name']}' для продавца '{seller_to_use.username}'."})
                    continue
            else:
                errors.append({"item": item_data_raw, "error": "Отсутствует обязательное поле 'name' для продукта."})
                continue

            if existing_product:
                # Если продукт существует, обновляем его
                serializer = ProductSerializer(existing_product, data=item_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    updated_products_count += 1
                else:
                    errors.append({"item": item_data_raw, "error": serializer.errors})
            else:
                # Если продукт не существует, создаем новый
                serializer = ProductSerializer(data=item_data)
                if serializer.is_valid():
                    serializer.save()
                    imported_products_count += 1
                else:
                    errors.append({"item": item_data_raw, "error": serializer.errors})

        response_data = {
            "message": "Импорт продуктов завершен.",
            "imported_count": imported_products_count,
            "updated_count": updated_products_count,
            "errors": errors,
        }

        if errors:
            # Возвращаем 207 Multi-Status, если были ошибки, но некоторые продукты были обработаны
            return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
        else:
            return Response(response_data, status=status.HTTP_200_OK)

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
        serializer = CategoryGetSerializer(data=request.query_params)
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

