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
        summary="Получить список продуктов",
        description="Получить список всех продуктов или отфильтровать по ID, названию или категории",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID продукта'
            ),
            OpenApiParameter(
                name='name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Название продукта'
            ),
            OpenApiParameter(
                name='categories',
                type={'type': 'array', 'items': {'type': 'number'}},
                location=OpenApiParameter.QUERY,
                description='Список ID категорий'
            )
        ],
        examples=[
            OpenApiExample(
                'Пример успешного ответа',
                value={
                    "message": "Продукт найден",
                    "product": {
                        "id": 1,
                        "name": "Телефон",
                        "price": 999.99,
                        "description": "Новый смартфон",
                        "quantity": 10,
                        "is_available": True,
                        "categories": [1, 2]
                    }
                },
                status_codes=['200'],
            )
        ]
    ),
    post=extend_schema(
        tags=['Продукты'],
        summary="Создать новый продукт",
        description="Создание нового продукта (требуются права add_product)",
        request=ProductAddSerializer, # Параметры теперь в теле запроса
        examples=[
            OpenApiExample(
                'Пример запроса',
                value={
                    "name": "Новый продукт",
                    "price": 100.50,
                    "description": "Описание продукта",
                    "quantity": 5,
                    "categories": [1, 2]
                },
                status_codes=['201'],
            ),
        ]
    ),
    put=extend_schema(
        tags=['Продукты'],
        summary="Обновить продукт",
        description="Обновление информации о продукте (требуются права update_product)",
        # Если ID продукта передаётся в URL (например, /products/{id}/), то здесь его не нужно
        # Если ID продукта передаётся в теле, используйте ProductUpdateSerializer
        request=ProductUpdateSerializer,
        examples=[
            OpenApiExample(
                'Пример запроса',
                value={
                    "id": 1, # Если ID передается в теле
                    "name": "Обновленное название",
                    "price": 120.50,
                    "description": "Новое описание",
                    "quantity": 8,
                    "is_available": True
                },
                status_codes=['200'],
            ),
        ]
    ),
    delete=extend_schema(
        tags=['Продукты'],
        summary="Удалить продукт",
        description="Удаление продукта (требуются права delete_product)",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID продукта',
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Продукт удален",
                response=ProductSearchSerializer,
                examples=[
                    OpenApiExample(
                        "Успешный ответ",
                        value={"message": "Продукт успешно удален"}
                    )
                ]
            ),
            404: OpenApiResponse(
                    description="Продукт не найден",
                    response=ProductSearchSerializer,
                    examples=[
                        OpenApiExample(
                            "Ошибка",
                            value={"message": "Продукт не найден"}
                        )
                    ]
                ),
            403: OpenApiResponse(
                description="Нет прав",
                response=ProductSearchSerializer,
                examples=[
                    OpenApiExample(
                        "Ошибка",
                        value={"message": "Недостаточно прав"}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                'Пример запроса',
                value={
                    "id": 1
                },
                status_codes=['200'],
            ),
        ],
    ),
    patch=extend_schema(
        tags=['Продукты'],
        summary="Добавить продукт в корзину",
        description="Добавление продукта в корзину пользователя (требуются права add_to_cart)",
        request=ProductAddToCartSerializer, # Параметры теперь в теле запроса
        responses={
            200: OpenApiResponse(
                description="Продукт добавлен в корзину",
                response=ProductAddToCartSerializer,
                examples=[
                    OpenApiExample(
                        "Успешный ответ",
                        value={
                            "message": "Продукт добавлен в корзину",
                            "cart_id": 1,
                            "product_id": 1,
                            "quantity": 2
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Недостаточно товара",
                response=ProductAddToCartSerializer,
                examples=[
                    OpenApiExample(
                        "Недостаточно товара",
                        value={"message": "Недостаточное количество товара"}
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Нет прав",
                response=ProductAddToCartSerializer,
                examples=[
                    OpenApiExample(
                        "Ошибка",
                        value={"message": "Недостаточно прав"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Продукт не найден",
                response=ProductAddToCartSerializer,
                examples=[
                    OpenApiExample(
                        "Ошибка",
                        value={"message": "Продукт не найден"}
                    )
                ]
            ),
            422: OpenApiResponse(
                description="Некорректные данные",
                response=ProductAddToCartSerializer,
                examples=[
                    OpenApiExample(
                        "Ошибка",
                        value={"message": "Некорректные данные"}
                    )
                ]
            )
        },
    )
)

products_change_schema = extend_schema_view(
    put=extend_schema(
        tags=['Продукты'],
        summary="Изменение доступности продукта (для продавцов)",
        description="""Изменение доступности продукта (требуются права change_product_availability)
        Передается ID продукта (необязательно) в теле запроса и доступность в теле запроса (Boolean)
        Если передан ID продукта, то изменяется доступность продукта с этим ID
        Если не передан ID продукта, то изменяется доступность всех продуктов продавца""",
        request=ProductChangeAvailabilitySerializer, # Параметры теперь в теле запроса
        examples=[
            OpenApiExample(
                'Пример запроса',
                value={
                    "id": 1,
                    "is_available": True
                }
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Доступность продукта изменена",
                response=ProductChangeAvailabilitySerializer,
                examples=[
                    OpenApiExample(
                        "Успешный ответ",
                        value={"message": "Доступность продукта изменена"}
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Нет прав",
                response=ProductChangeAvailabilitySerializer,
                examples=[
                    OpenApiExample(
                        "Ошибка",
                        value={"message": "Недостаточно прав"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Продукт не найден",
                response=ProductChangeAvailabilitySerializer,
                examples=[
                    OpenApiExample(
                        "Ошибка",
                        value={"message": "Продукт не найден"}
                    )
                ]
            ),
            422: OpenApiResponse(
                description="Некорректные данные",
                response=ProductChangeAvailabilitySerializer,
                examples=[
                    OpenApiExample(
                        "Ошибка",
                        value={"message": "Некорректные данные"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Недостаточно товара",
                response=ProductChangeAvailabilitySerializer,
                examples=[
                    OpenApiExample(
                        "Недостаточно товара",
                        value={"message": "Недостаточное количество товара"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Продукт недоступен",
                response=ProductChangeAvailabilitySerializer,
                examples=[
                    OpenApiExample(
                        "Продукт недоступен",
                        value={"message": "Продукт недоступен"}
                    )
                ]
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
                    "id": 1,
                    "name": "Обновленное название",
                    "description": "Новое описание"
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
                description='ID категории'
            ),
            OpenApiParameter(
                name='name',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Название категории'
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


__all__ = ['products_list_schema', 'categories_view_schema', 'cart_view_schema', 'products_change_schema']