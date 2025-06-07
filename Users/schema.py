from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
    OpenApiResponse,
    OpenApiExample,
    OpenApiParameter
)
from drf_spectacular.types import OpenApiTypes
from Users.serializers import *


user_register_schema = extend_schema(
    tags=['Пользователи'],
    summary="Регистрация нового пользователя",
    description="""Создает нового пользователя (покупателя, продавца или администратора),
                   Требуются права `Users.add_user`.
                   Принимает user_type, email, password, username, first_name, last_name, phone_number
                   Проверяется уникальность email и username.

    """,
    request=UserSerializer,
    responses={
        201: OpenApiResponse(
            description="Пользовтель успешно зарегистрирован",
            response=UserSerializer,
            examples=[
                OpenApiExample(
                    "Пользователь успешно зарегистрирован",
                    value={
                        "message": "Пользователь успешно зарегистрирован",
                        "data": {
                            "user_type": "Buyer",
                            "email": "user@example.com",
                            "username": "Cappucino",
                            "first_name": "string",
                            "last_name": "string",
                            "phone_number": "string"
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="Неверные данные",
            response=UserSerializer,
            examples=[
                OpenApiExample(
                    "Неверные данные",
                    value={
                        "message": "Неверные данные",
                        "errors": {
                            "username": [
                                "A user with that username already exists."
                            ]
                        }
                    }
                )
            ]
        )
    }
)

user_login_schema = extend_schema(
    tags=['Пользователи'],
    summary="Аутентификация пользователя",
    description="Вход пользователя по логину и паролю",
    request=LoginSerializer,  # Parameters 'username' and 'password' are expected in LoginSerializer
    responses={
        200: OpenApiResponse(
            description="Успешный вход",
            response=LoginSerializer,
            examples=[
                OpenApiExample(
                    "Успешный ответ",
                    value={"message": "Успешная аутентификация"}
                )
            ]
        ),
        400: OpenApiResponse(
            description="Ошибка аутентификации",
            response=LoginSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"message": "Неверные данные"}
                )
            ]
        )
    }
)

user_logout_schema = extend_schema(
    tags=['Пользователи'],
    summary="Выход пользователя",
    description="Завершает сеанс пользователя",
    request=None,
    # No request body typically needed for logout
    responses={
        200: OpenApiResponse(
            description="Успешный выход",
            response=OpenApiTypes.STR,
            examples=[
                OpenApiExample(
                    "Успешный ответ",
                    value={"message": "Успешный выход"}
                )
            ]
        )
    }
)

user_change_password_schema = extend_schema(
    tags=['Пользователи'],
    summary="Изменение пароля",
    description="Смена пароля пользователя (требуется старый пароль)",
    request=ChangePasswordSerializer,  # 'old_password' and 'new_password' expected in ChangePasswordSerializer
    responses={
        200: OpenApiResponse(
            description="Пароль изменен",
            response=ChangePasswordSerializer,
            examples=[
                OpenApiExample(
                    "Успешный ответ",
                    value={"message": "Пароль успешно изменен"}
                )
            ]
        ),
        400: OpenApiResponse(
            description="Ошибка валидации",
            response=ChangePasswordSerializer,
            examples=[
                OpenApiExample(
                    "Неверный старый пароль",
                    value={"message": "Неверный старый пароль"}
                ),
                OpenApiExample(
                    "Пароли совпадают",
                    value={"message": "Новый пароль не может совпадать со старым"}
                )
            ]
        ),
        401: OpenApiResponse(
            description="Не авторизован",
            response=ChangePasswordSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"message": "Пользователь не аутентифицирован"}
                )
            ]
        ),
        403: OpenApiResponse(
            description="Нет прав",
            response=ChangePasswordSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"message": "Недостаточно прав"}
                )
            ]
        )
    }
)

delete_user_schema = extend_schema(
    tags=['Пользователи'],
    summary="Удаление пользователя",
    description="Удаляет текущего пользователя или другого (для админов)",
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='ID пользователя',
        )
    ],
    examples=[
        OpenApiExample(
            "Удаление текущего пользователя",
            value={},
            status_codes=['200'],
            summary="Удаление текущего пользователя",
            description="Удаление текущего пользователя (требуются права delete_user)",
        ),
        OpenApiExample(
            "Удаление другого пользователя",
            value={"id": 2}
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Пользователь удален",
            response=DeleteUserSerializer,
            examples=[
                OpenApiExample(
                    "Успешный ответ",
                    value={"message": "Пользователь успешно удален"}
                )
            ]
        ),
        401: OpenApiResponse(
            description="Не авторизован / Нет прав",
            response=DeleteUserSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"message": "Недостаточно прав"}
                )
            ]
        )
    }
)

update_user_schema = extend_schema(
    tags=['Пользователи'],
    summary="Обновление данных пользователя",
    description="Изменяет информацию о пользователе",
    request=UserUpdateSerializer,  # All update parameters are in UserUpdateSerializer
    responses={
        200: OpenApiResponse(
            description="Данные обновлены",
            response=UserUpdateSerializer,
            examples=[
                OpenApiExample(
                    "Успешный ответ",
                    value={
                        "username": "updated_user",
                        "email": "new@example.com"
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="Ошибка валидации",
            response=UserUpdateSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"email": ["Введите правильный email."]}
                )
            ]
        ),
        401: OpenApiResponse(
            description="Не авторизован",
            response=UserUpdateSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"message": "Пользователь не аутентифицирован"}
                )
            ]
        ),
        403: OpenApiResponse(
            description="Нет прав",
            response=UserUpdateSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"message": "Недостаточно прав"}
                )
            ]
        ),
        404: OpenApiResponse(
            description="Пользователь не найден",
            response=UserUpdateSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"message": "Пользователь не найден"}
                )
            ]
        )
    }
)

# Renamed from update_user_data_schema to avoid duplication with update_user_schema
# This seems to be a duplicate of update_user_schema, consider if you need both.
# If it's for a different endpoint, the name should reflect that.
# Assuming this is intended for a separate endpoint that also updates user data.
update_user_data_schema = extend_schema(
    tags=['Пользователи'],
    summary="Обновление данных пользователя",
    description="Изменяет информацию о пользователе",
    request=UserUpdateSerializer, # All parameters are in UserUpdateSerializer
    responses={
        200: OpenApiResponse(
            description="Данные обновлены",
            response=UserUpdateSerializer,
            examples=[
                OpenApiExample(
                    "Успешный ответ",
                    value={
                        "username": "updated_user",
                        "email": "new@example.com"
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="Ошибка валидации",
            response=UserUpdateSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={
                        "email": "Введите правильный email"
                    }
                )
            ]
        ),
        401: OpenApiResponse(
            description="Не авторизован",
            response=UserUpdateSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"message": "Пользователь не аутентифицирован"}
                )
            ]
        ),
        403: OpenApiResponse(
            description="Нет прав",
            response=UserUpdateSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"message": "Недостаточно прав"}
                )
            ]
        ),
        404: OpenApiResponse(
            description="Пользователь не найден",
            response=UserUpdateSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"message": "Пользователь не найден"}
                )
            ]
        )
    }
)

delete_user_data_schema = extend_schema(
    tags=['Пользователи'],
    summary="Удаление данных пользователя",
    description="""Очищает указанные поля пользователя (email, phone и т.д.). 
                   Принимает название полей в data_to_delete либо список полей.
                   Админы могут удалять данные других пользователей по id. 
                   Требуется аутентификация и права delete_user_data""",
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='ID пользователя'
        ),
        OpenApiParameter(
            name='data_to_delete',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Название поля или список полей, которые нужно удалить'
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Данные удалены",
            examples=[
                OpenApiExample(
                    "Успешный ответ",
                    value={"message": "Данные пользователя успешно удалены"}
                )
            ]
        ),
        400: OpenApiResponse(
            description="Ошибка валидации",
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"data_to_delete": ["Это поле обязательно."]}
                )
            ]
        ),
        401: OpenApiResponse(
            description="Не авторизован",
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"message": "Пользователь не аутентифицирован"}
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
            description="Пользователь не найден",
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"message": "Пользователь не найден"}
                )
            ]
        )
    }
)


get_user_data_schema = extend_schema(
    tags=['Пользователи'],
    summary="Получение данных пользователя",
    description="""Возвращает информацию о пользователе (Админы могут получать данные 
                    других пользователей, нужны права get_user_data).
                    Для получения данных другого пользователя нужно передать id""",
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='ID пользователя'
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Данные пользователя успешно получены",
            response=UserSerializer, # Assuming UserSerializer is the response format
            examples=[
                OpenApiExample(
                    "Успешный ответ",
                    value={
                        "id": 1,
                        "username": "test_user",
                        "email": "user@example.com"
                    }
                )
            ]
        ),
        401: OpenApiResponse(
            description="Не авторизован",
            response=GetUserDataSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"message": "Недостаточно прав"}
                )
            ]
        ),
        404: OpenApiResponse(
            description="Пользователь не найден",
            response=GetUserDataSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"message": "Пользователь не найден"}
                )
            ]
        )
    }
)

restore_password_schema = extend_schema(
    tags=['Пользователи'],
    summary="Восстановление пароля",
    description="Генерирует новый пароль и отправляет на email. Для работы функции необходима настрйка сервера почты",
    request=RestorePasswordSerializer,  # 
    responses={
        200: OpenApiResponse(
            description="Пароль изменен",
            response=RestorePasswordSerializer,
            examples=[
                OpenApiExample(
                    "Успешный ответ",
                    value={"message": "Пароль успешно изменен"}
                )
            ]
        ),
        400: OpenApiResponse(
            description="Ошибка валидации",
            response=RestorePasswordSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"email": ["Введите правильный email."]}
                )
            ]
        ),
        404: OpenApiResponse(
            description="Пользователь не найден",
            response=RestorePasswordSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"message": "Пользователь с таким email не найден"}
                )
            ]
        )
    }
)

contact_schema = extend_schema_view(
    post=extend_schema(
        tags=['Контакты пользователя'], 
        summary="Добавление нового контакта",
        description="""
        Добавляет новый контакт для текущего пользователя.
        Требует прав: Users.add_contact
        Максимальное количество контактов - 5.
        """,
        request=AddContactSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            422: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Успешное добавление',
                value={'message': 'Контакт успешно добавлен'},
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                'Ошибка валидации',
                value={'message': 'Обязательные поля не заполнены'},
                response_only=True,
                status_codes=['422']
            ),
            OpenApiExample(
                'Ошибка прав',
                value={'message': 'Недостаточно прав'},
                response_only=True,
                status_codes=['401']
            ),
            OpenApiExample(
                'Превышение лимита',
                value={'message': 'Превышено максимальное количество контактов'},
                response_only=True,
                status_codes=['400']
            ),
        ]
    ),
    put=extend_schema(
        tags=['Контакты пользователя'],
        summary="Изменение контакта",
        description="""
        Изменяет существующий контакт по ID.
        Требует прав: Users.change_contact
        """,
        request=UpdateContactSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            422: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Успешное изменение',
                value={'message': 'Контакт успешно изменен'},
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                'Контакт не найден',
                value={'message': 'Контакт не найден'},
                response_only=True,
                status_codes=['404']
            ),
        ]
    ),
    delete=extend_schema(
        tags=['Контакты пользователя'],
        summary="Удаление контакта",
        description="""
        Удаляет контакт по ID.
        Требует прав: Users.delete_contact
        """,
        request=DeleteContactSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Успешное удаление',
                value={'message': 'Контакт успешно удален'},
                response_only=True,
                status_codes=['200']
            ),
        ]
    ),
    get=extend_schema(
        tags=['Контакты пользователя'],
        summary="Получение контакта(ов)",
        description="""
        Получает контакт по ID или все контакты пользователя.
        Требует прав: Users.view_contact
        """,
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID контакта (необязательный)',
                required=False
            ),
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            422: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Успешное получение одного контакта',
                value={'contact': {'id': 1, 'name': 'Иван', 'phone': '+79991234567'}},
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                'Успешное получение всех контактов',
                value={'contacts': [{'id': 1, 'name': 'Иван', 'phone': '+79991234567'}, {'id': 2, 'name': 'Петр', 'phone': '+79997654321'}]},
                response_only=True,
                status_codes=['200']
            ),
        ]
    ),
)
        

__all__ = [
    'get_user_data_schema',
    'update_user_data_schema',
    'delete_user_data_schema',
    'restore_password_schema',
    'user_register_schema',
    'user_change_password_schema',
    'delete_user_schema',
    'user_login_schema',
    'user_logout_schema',
    'contact_schema'
]