from drf_spectacular.utils import (
    extend_schema, 
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
    OpenApiResponse,
    OpenApiExample,
    inline_serializer
)
from rest_framework import serializers
from .serializers import *



products_list_schema = extend_schema_view(
    get=extend_schema(
        tags=['Продукты'],

        summary="Получить список продуктов или конкретный продукт",
        description="""
        Возвращает список всех продуктов, либо фильтрует по `id`, `name`, или `categories`.
        Если ни один параметр не указан, возвращает все продукты.
        Если указаны `id` или `name`, пытается найти один продукт.
        Если указаны `categories`, возвращает все продукты из указанных категорий.
        """,
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY, # Предполагаем, что GET-параметры передаются через query
                required=False,
                description="Идентификатор продукта для поиска.",
                examples=[OpenApiExample("Поиск по ID", value=1)]
            ),
            OpenApiParameter(
                name="name",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Название продукта для поиска.",
                examples=[OpenApiExample("Поиск по названию", value="Смартфон")]
            ),
            OpenApiParameter(
                name="categories",
                type=OpenApiTypes.STR, # List of ints as comma-separated string for query params
                location=OpenApiParameter.QUERY,
                required=False,
                description="Список идентификаторов категорий через запятую (например, '1,5,10').",
                examples=[OpenApiExample("Поиск по категориям", value=[1, 5, 10])]
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=ProductsListSerializer(many=True),
                description="Успешный поиск продуктов. Может вернуть список или один продукт.",
                examples=[
                    OpenApiExample(
                        "Все продукты",
                        value={"message": "Все продукты", "products": [{"id": 1, "name": "Тестовый продукт", "price": "100.00"}]},
                        response_only=True
                    ),
                    OpenApiExample(
                        "Продукт найден",
                        value={"message": "Продукт найден", "product": {"id": 1, "name": "Тестовый продукт", "price": "100.00"}},
                        response_only=True
                    )
                ]
            ),
            400: OpenApiResponse(
                response={"message": "Ошибка валидации"},
                description="Неверные параметры запроса.",
                examples=[OpenApiExample("Неверные параметры", value={"message": "Неверные параметры запроса"})]
            ),
            404: OpenApiResponse(
                response={"message": "Продукт не найден"},
                description="Продукт по указанным параметрам не найден.",
                examples=[OpenApiExample("Продукт не найден", value={"message": "Продукт не найден"})]
            )
        }
    ),
    post=extend_schema(
        tags=['Продукты'],
        summary="Создать новый продукт",
        description="Создает новый продукт. Требуются права `Users.add_product`.",
        request=ProductSerializer,
        responses={
            201: OpenApiResponse(
                response=inline_serializer(
                    name='ProductCreationResponse',
                    fields={
                        'message': serializers.CharField(),
                        'id': serializers.IntegerField(),
                        'name': serializers.CharField(),
                        'categories': serializers.ListField(child=serializers.CharField())
                    }
                ),
                description="Продукт успешно создан.",
                examples=[
                    OpenApiExample(
                        "Успешное создание",
                        value={
                            "message": "Продукт успешно создан",
                            "id": 1,
                            "name": "Новый продукт",
                            "categories": ["Категория 1", "Категория 2"]
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Недостаточно прав. Пользователь не аутентифицирован."),
            403: OpenApiResponse(description="Недостаточно прав. Пользователь не имеет необходимых разрешений."),
            422: OpenApiResponse(
                response=ProductSerializer,
                description="Некорректные данные продукта.",
                examples=[OpenApiExample("Ошибка валидации", value={"name": ["Это поле обязательно."]})]
            )
        }
    ),
    put=extend_schema(
        tags=['Продукты'],
        summary="Изменить существующий продукт",
        description="Обновляет информацию о продукте. Требуются права `Users.update_product`.",
        request=ProductUpdateSerializer,
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='ProductUpdateResponse',
                    fields={
                        'message': serializers.CharField(),
                        'product': ProductSerializer()
                    }
                ),
                description="Продукт успешно изменен.",
                examples=[
                    OpenApiExample(
                        "Успешное изменение",
                        value={"message": "Продукт успешно изменен", "product": {"id": 1, "name": "Обновленный продукт", "price": "120.00"}}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Ошибка валидации или продукт с таким названием уже существует.",
                examples=[
                    OpenApiExample("Ошибка валидации", value={"price": ["Введите действительное число."]}),
                    OpenApiExample("Продукт с таким названием существует", value={"message": "Продукт с таким названием уже существует"})
                ]
            ),
            401: OpenApiResponse(description="Пользователь не аутентифицирован."),
            403: OpenApiResponse(description="Недостаточно прав."),
            404: OpenApiResponse(description="Продукт не найден.")
        }
    ),
    delete=extend_schema(
        tags=['Продукты'],
        summary="Удалить продукт",
        description="Удаляет продукт по `id` или `name`. Требуются права `Users.delete_product`.",
        request=ProductSearchSerializer,
        responses={
            200: OpenApiResponse(description="Продукт успешно удален.", examples=[OpenApiExample("Успешное удаление", value={"message": "Продукт успешно удален"})]),
            400: OpenApiResponse(description="Неверные параметры запроса.", examples=[OpenApiExample("Ошибка валидации", value={"id": ["Это поле обязательно."]})]),
            401: OpenApiResponse(description="Пользователь не аутентифицирован."),
            403: OpenApiResponse(description="Недостаточно прав."),
            404: OpenApiResponse(description="Продукт не найден.")
        }
    ),
    patch=extend_schema(
        tags=['Продукты'],
        summary="Добавить продукт в корзину",
        description="Добавляет указанное количество продукта в корзину текущего пользователя. Требуются права `Users.add_to_cart`.",
        request=ProductAddToCartSerializer,
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='AddToCartResponse',
                    fields={
                        'message': serializers.CharField(),
                        'cart_id': serializers.IntegerField(),
                        'product_id': serializers.IntegerField(),
                        'quantity': serializers.IntegerField()
                    }
                ),
                description="Продукт добавлен в корзину.",
                examples=[
                    OpenApiExample(
                        "Успешное добавление в корзину",
                        value={"message": "Продукт добавлен в корзину", "cart_id": 1, "product_id": 1, "quantity": 2}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Недостаточное количество товара или продукт недоступен.",
                examples=[
                    OpenApiExample("Недостаточно товара", value={"message": "Недостаточное количество товара"}),
                    OpenApiExample("Продукт недоступен", value={"message": "Продукт недоступен для заказа"})
                ]
            ),
            403: OpenApiResponse(description="Недостаточно прав."),
            404: OpenApiResponse(description="Продукт не найден."),
            422: OpenApiResponse(
                response=ProductAddToCartSerializer,
                description="Некорректные данные запроса.",
                examples=[OpenApiExample("Ошибка валидации", value={"id": ["Это поле обязательно."]})]
            )
        }
    )
)

products_change_schema = extend_schema_view(
    put=extend_schema(
        tags=['Продукты'],
        summary="Изменить доступность продуктов",
        description="""
        Изменяет доступность (`is_available`) одного или всех продуктов продавца.
        Если `id` продукта не указан, меняет доступность для всех продуктов текущего продавца.
        Требуются права `Users.change_product_availability`.
        """,
        request=ProductChangeAvailabilitySerializer,
        responses={
            200: OpenApiResponse(description="Доступность продуктов/продукта успешно изменена."),
            400: OpenApiResponse(description="Неверные данные запроса (например, `id` не найден)."),
            403: OpenApiResponse(description="Недостаточно прав."),
            401: OpenApiResponse(description="Пользователь не аутентифицирован.") # Добавлено, если AccessCheck требует аутентификации
        }
    ),
    post=extend_schema(
        tags=['Продукты'],
        summary="Добавить параметры товару",
        description="""
        Добавляет новые параметры к указанному продукту.
        Параметры относятся только к продуктам текущего продавца.
        Требуются права `Users.add_product_parameters`.
        """,
        request=CreateParametersSerializer,
        responses={
            200: OpenApiResponse(description="Параметры продукта успешно добавлены."),
            400: OpenApiResponse(description="Ошибка запроса: ID продукта не передан или продукт относится к другому продавцу."),
            403: OpenApiResponse(description="Недостаточно прав."),
            422: OpenApiResponse(
                response=CreateParametersSerializer,
                description="Некорректные данные валидации."
            )
        }
    ),
    delete=extend_schema(
        tags=['Продукты'],
        summary="Удалить параметры товара",
        description="""
        Удаляет один или все параметры для указанного продукта.
        Если `parameters_id` не указан, удаляет все параметры продукта.
        Параметры относятся только к продуктам текущего продавца.
        Требуются права `Users.delete_product_parameters`.
        """,
        request=DeleteParametersSerializer,
        responses={
            200: OpenApiResponse(description="Параметры продукта успешно удалены."),
            400: OpenApiResponse(description="Продукт относится к другому продавцу."),
            403: OpenApiResponse(description="Недостаточно прав."),
            404: OpenApiResponse(description="Такого параметра не существует."),
            422: OpenApiResponse(
                response=DeleteParametersSerializer,
                description="Некорректные данные валидации."
            )
        }
    ),
    patch=extend_schema(
        tags=['Продукты'],
        summary="Изменить параметры товара",
        description="""
        Изменяет существующие параметры для указанного продукта.
        Требуются права `Users.update_product_parameters`.
        """,
        request=UpdateParametersSerializer,
        responses={
            200: OpenApiResponse(description="Параметры продукта успешно изменены."),
            400: OpenApiResponse(description="Ошибка запроса: ID продукта не передан или продукт относится к другому продавцу."),
            403: OpenApiResponse(description="Недостаточно прав."),
            404: OpenApiResponse(description="Такого параметра не существует."),
            422: OpenApiResponse(
                response=UpdateParametersSerializer,
                description="Некорректные данные валидации."
            )
        }
    )
)

categories_view_schema = extend_schema_view(
    post=extend_schema(
        tags=['Категории продуктов'],
        summary="Создать категорию",
        description="Создание новой категории (требуются права create_category)",
        request=CategorySerializer, # Параметры теперь в теле запроса
        examples=[
            OpenApiExample(
                'Пример запроса',
                value={
                    "name": "Новая категория",
                    "description": "Описание категории"
                },
                status_codes=['201'],
            ),
        ]
    ),
    delete=extend_schema(
        tags=['Категории продуктов'],
        summary="Удалить категорию",
        description="Удаление категории (требуются права delete_category)",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID категории',
                required=True
            )
        ],
        examples=[
            OpenApiExample(
                'Пример запроса',
                value={
                    "id": 1
                },
                status_codes=['200'],
            ),
        ]
    ),
    put=extend_schema(
        tags=['Категории продуктов'],
        summary="Обновить категорию",
        description="Обновление информации о категории (требуются права update_category)",
        request=CategoryUpdateSerializer, # Параметры теперь в теле запроса
        examples=[
            OpenApiExample(
                'Пример запроса',
                value={
                    "id": 1, #id
                    "name": "Обновленное название", #name
                    "description": "Новое описание" #description
                },
                status_codes=['200'],
            ),
        ]
    ),
    get=extend_schema(
        tags=['Категории продуктов'],
        summary="Получить категории",
        description="Получение списка всех категорий или конкретной категории по ID/названию",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID категории',
                required=False
            ),
            OpenApiParameter(
                name='name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Название категории',
                required=False
            )
        ],
        examples=[
            OpenApiExample(
                'Пример успешного ответа',
                value={
                    "message": "Категория найдена",
                    "id": 1,
                    "name": "Электроника"
                },
                status_codes=['200'],
            ),
        ]
    ),
)

cart_view_schema = extend_schema_view(
    get=extend_schema(
        tags=['Корзина'],
        summary="Получить корзину",
        description="Получение содержимого корзины текущего пользователя",
        responses={
            200: inline_serializer(
                name='CartResponse',
                fields={
                    'message': serializers.CharField(),
                    'id': serializers.IntegerField(),
                    'Cart_products': serializers.ListField(),
                    'Total_price': serializers.DecimalField(max_digits=10, decimal_places=2)
                }
            )
        },
        examples=[
            OpenApiExample(
                'Пример успешного ответа',
                value={
                    "message": "Корзина успешно получена",
                    "id": 1,
                    "Cart_products": [
                        {
                            "name": "Телефон",
                            "quantity": 1,
                            "price": "999.99",
                            "id": 1,
                            "is_available": True,
                            "seller": "seller1"
                        }
                    ],
                    "Total_price": "999.99"
                },
                status_codes=['200'],
            ),
        ]
    ),
    delete=extend_schema(
        tags=['Корзина'],
        summary="Удалить продукт из корзины",
        description="Удаление продукта из корзины по ID продукта",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID продукта',
                required=True
            )
        ],
        examples=[
            OpenApiExample(
                'Пример запроса',
                value={
                    "id": 1
                },
                status_codes=['200'],
            ),
        ]
    ),
    put=extend_schema(
        tags=['Корзина'],
        summary="Обновить продукт в корзине",
        description="Обновление количества продукта в корзине",
        request=CartProductSearchSerializer, # Параметры теперь в теле запроса (id и quantity)
        examples=[
            OpenApiExample(
                'Пример запроса',
                value={
                    "id": 1,
                    "quantity": 3
                },
                status_codes=['200'],
            ),
        ]
    ),
    post=extend_schema(
        tags=['Корзина'],
        summary="Оформить заказ",
        description="Оформление заказа из содержимого корзины",
        # Здесь нет параметров для тела запроса, так как заказ оформляется из содержимого корзины,
        # которая уже существует для пользователя. Если бы были дополнительные параметры для заказа,
        # их можно было бы добавить через 'request'.
        responses={
            201: inline_serializer(
                name='OrderResponse',
                fields={
                    'message': serializers.CharField(),
                    'id': serializers.IntegerField(),
                    'total_price': serializers.DecimalField(max_digits=10, decimal_places=2),
                    'order_products': serializers.ListField(child=serializers.CharField())
                }
            )
        },
        examples=[
            OpenApiExample(
                'Пример успешного ответа',
                value={
                    "message": "Заказ успешно оформлен",
                    "id": 5,
                    "total_price": "1999.98",
                    "order_products": ["Телефон", "Наушники"]
                },
                status_codes=['201'],
            ),
        ]
    ),
)

product_import_schema = extend_schema_view(
    post=extend_schema(
        tags=['Продукты'],
        summary="Импорт продуктов из YAML файла",
        description="""
        Импортирует данные о продуктах из предоставленного YAML файла. 
        YAML файл должен содержать верхнеуровневые ключи 'shop', 'categories' и 'goods'.
        Продукты в 'goods' могут содержать 'category' (по ID из верхнеуровневых категорий)
        и 'parameters' (как словарь ключ-значение).
        Если 'seller_id' не указан для продукта, используется текущий аутентифицированный пользователь.
        Существующие продукты (по имени и продавцу) будут обновлены.
        """,
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "format": "binary",
                        "description": "Файл YAML с данными о продуктах."
                    }
                },
                "required": ["file"],
            }
        },
        responses={
            200: ProductImportSuccessSerializer,
            207: ProductImportSuccessSerializer, # Multi-Status для частичного успеха/ошибок
            400: ProductImportErrorSerializer,
            500: ProductImportErrorSerializer,
        },
        examples=[
            OpenApiExample(
                'Пример успешного ответа',
                value={
                    "message": "Импорт продуктов завершен.",
                    "imported_count": 2,
                    "updated_count": 1,
                    "errors": []
                },
                response_only=True,
                status_codes=["200", "207"]
            ),
            OpenApiExample(
                'Пример ответа с ошибками',
                value={
                    "message": "Импорт продуктов завершен.",
                    "imported_count": 1,
                    "updated_count": 0,
                    "errors": [
                        {"item": {"name": "Невалидный продукт"}, "error": {"name": ["Это поле обязательно."]}}
                    ]
                },
                response_only=True,
                status_codes=["207"]
            ),
            OpenApiExample(
                'Пример ошибки запроса',
                value={"error": "Файл YAML не был предоставлен."},
                response_only=True,
                status_codes=["400"]
            ),
        ]
    )
)



__all__ = ['products_list_schema', 'categories_view_schema', 'cart_view_schema', 'products_change_schema', 'product_import_schema']