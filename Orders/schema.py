from drf_spectacular.utils import (
    extend_schema, 
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
    OpenApiResponse,
    OpenApiExample
)
from Orders.serializers import OrderProductSerializer, OrderSearchSerializer, OrderStatusUpdateSerializer


order_list_schema = extend_schema_view(
    get = extend_schema(
        tags=['Заказы'],
        summary="Получение заказов",
        description="Получение заказа по id или списка заказов (если id не передан) для текущего пользователя (покупателя, продавца или админа)",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID заказа (опционально)',
                required=False
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Список заказов",
                response=OrderProductSerializer,
                examples=[
                    OpenApiExample(
                        "Пример ответа (покупатель)",
                        value={
                            "message": "Все заказы",
                            "orders": [
                                {
                                    "id": 1,
                                    "product": "Телефон",
                                    "quantity": 1,
                                    "status": "Delivered",
                                    "seller": "seller1"
                                }
                            ]
                        }
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Нет прав",
                examples=[
                    OpenApiExample(
                        "Ошибка",
                        value={"message": "Недостаточно прав"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Заказ не найден",
                examples=[
                    OpenApiExample(
                        "Ошибка",
                        value={"message": "Заказ не найден"}
                    )
                ]
            )
        }
    ),
    put = extend_schema(
        tags=['Заказы'],
        summary="Изменить статус заказа",
        description="Обновление статуса заказа по id (требуются права update_order_status)",
        request=OrderStatusUpdateSerializer,
        responses={
            200: OpenApiResponse(
                description="Статус изменен",
                examples=[
                    OpenApiExample(
                        "Успешный ответ",
                        value={
                            "message": "Статус заказа успешно изменен",
                            "order_product": 1,
                            "status": "Shipped"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Ошибка валидации",
                examples=[
                    OpenApiExample(
                        "Статус не изменился",
                        value={"message": "Статус заказа не изменился"}
                    ),
                    OpenApiExample(
                        "Ошибка в данных",
                        value={"status": ["Недопустимый статус"]}
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Нет прав",
                examples=[
                    OpenApiExample(
                        "Ошибка",
                        value={"message": "Недостаточно прав"}
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Заказ не найден",
                examples=[
                    OpenApiExample(
                        "Ошибка",
                        value={"message": "Заказ не найден"}
                    )
                ]
            )
        }
    )
)