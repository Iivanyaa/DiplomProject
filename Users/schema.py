from drf_spectacular.utils import (
    extend_schema, 
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
    OpenApiResponse,
    OpenApiExample
)
from Users.serializers import UserRegSerializer, LoginSerializer, ChangePasswordSerializer, DeleteUserSerializer, GetUserDataSerializer, DeleteUserDataSerializer, RestorePasswordSerializer, UserUpdateSerializer, RestorePasswordSerializer


user_register_schema = extend_schema(
    tags=['Пользователи'],
    summary="Регистрация нового пользователя",
    description="Создает нового пользователя (покупателя, продавца или администратора)",
    request=UserRegSerializer,
    parameters=[
        OpenApiParameter(
            name="username",
            description="Логин пользователя",
            required=True,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="email",
            description="Почта пользователя",
            required=True,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="password",
            description="Пароль пользователя",
            required=True,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="user_type",
            description="Тип пользователя",
            required=True,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="first_name",
            description="Имя пользователя",
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="last_name",
            description="Фамилия пользователя",
            required=False,
            type=OpenApiTypes.STR
        )
    ],
    responses={
        201: OpenApiResponse(
            description="Успешная регистрация",
            response=UserRegSerializer,
            examples=[
                OpenApiExample(
                    "Успешный ответ",
                    value={
                        "id": 1,
                        "username": "new_user",
                        "email": "user@example.com",
                        "user_type": "Buyer"
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="Ошибка валидации",
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={
                        "username": ["Это поле обязательно."],
                        "email": ["Введите правильный email."]
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
    request=LoginSerializer,
    parameters=[
        OpenApiParameter(
            name="username",
            description="Логин пользователя",
            required=True,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="password",
            description="Пароль пользователя",
            required=True,
            type=OpenApiTypes.STR
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Успешный вход",
            examples=[
                OpenApiExample(
                    "Успешный ответ",
                    value={"message": "Успешная аутентификация"}
                )
            ]
        ),
        400: OpenApiResponse(
            description="Ошибка аутентификации",
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
    responses={
        200: OpenApiResponse(
            description="Успешный выход",
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
    request=ChangePasswordSerializer,
    parameters=[
        OpenApiParameter(
            name="old_password",
            description="Старый пароль пользователя",
            required=True,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="new_password",
            description="Новый пароль пользователя",
            required=True,
            type=OpenApiTypes.STR
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Пароль изменен",
            examples=[
                OpenApiExample(
                    "Успешный ответ",
                    value={"message": "Пароль успешно изменен"}
                )
            ]
        ),
        400: OpenApiResponse(
            description="Ошибка валидации",
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
        )
    }
)

delete_user_schema = extend_schema(
    tags=['Пользователи'],
    summary="Удаление пользователя",
    description="Удаляет текущего пользователя или другого (для админов)",
    request=DeleteUserSerializer,
    parameters=[
        OpenApiParameter(
            name="id",
            description="ID пользователя",
            required=False,
            type=OpenApiTypes.INT
        ),
        OpenApiParameter(
            name="username",
            description="Username пользователя",
            required=False,
            type=OpenApiTypes.STR
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Пользователь удален",
            examples=[
                OpenApiExample(
                    "Успешный ответ",
                    value={"message": "Пользователь успешно удален"}
                )
            ]
        ),
        401: OpenApiResponse(
            description="Не авторизован / Нет прав",
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
    request=UserUpdateSerializer,
    parameters=[
        OpenApiParameter(
            name="id",
            description="ID пользователя",
            required=False,
            type=OpenApiTypes.INT
        ),
        OpenApiParameter(
            name="username",
            description="Username пользователя",
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="email",
            description="Email пользователя",
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="first_name",
            description="Имя пользователя",
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="last_name",
            description="Фамилия пользователя",
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="phone_number",
            description="Номер телефона пользователя",
            required=False,
            type=OpenApiTypes.STR
        )
    ],
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
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"email": ["Введите правильный email."]}
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

update_user_data_schema = extend_schema(
    tags=['Пользователи'],
    summary="Обновление данных пользователя",
    description="Изменяет информацию о пользователе",
    request=UserUpdateSerializer,
    parameters=[
        OpenApiParameter(
            name="id",
            description="ID пользователя",
            required=False,
            type=OpenApiTypes.INT
        ),
        OpenApiParameter(
            name="username",
            description="Username пользователя",
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="email",
            description="Email пользователя",
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="first_name",
            description="Имя пользователя",
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="last_name",
            description="Фамилия пользователя",
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="phone_number",
            description="Номер телефона пользователя",
            required=False,
            type=OpenApiTypes.STR
        )
    ],
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
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"email": ["Введите правильный email."]}
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

delete_user_data_schema = extend_schema(
    tags=['Пользователи'],
    summary="Удаление данных пользователя",
    description="Очищает указанные поля пользователя (email, phone и т.д.)",
    request=DeleteUserDataSerializer,
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
    description="Возвращает информацию о пользователе (для себя или админов)",
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='ID пользователя (опционально)',
            required=False
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Данные получены",
            response=UserRegSerializer,
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

restore_password_schema = extend_schema(
    tags=['Пользователи'],
    summary="Восстановление пароля",
    description="Генерирует новый пароль и отправляет на email",
    request=RestorePasswordSerializer,
    responses={
        200: OpenApiResponse(
            description="Пароль изменен",
            examples=[
                OpenApiExample(
                    "Успешный ответ",
                    value={"message": "Пароль успешно изменен"}
                )
            ]
        ),
        400: OpenApiResponse(
            description="Ошибка валидации",
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"email": ["Введите правильный email."]}
                )
            ]
        ),
        404: OpenApiResponse(
            description="Пользователь не найден",
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"message": "Пользователь с таким email не найден"}
                )
            ]
        )
    }
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
    'user_logout_schema'
]
