from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
    OpenApiParameter
)
from drf_spectacular.types import OpenApiTypes
from Users.serializers import (
    UserRegSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    DeleteUserSerializer,
    GetUserDataSerializer, # Assuming this serializer is used for retrieving user data in the body if needed
    DeleteUserDataSerializer,
    RestorePasswordSerializer,
    UserUpdateSerializer,
)


user_register_schema = extend_schema(
    tags=['Пользователи'],
    summary="Регистрация нового пользователя",
    description="Создает нового пользователя (покупателя, продавца или администратора)",
    request=UserRegSerializer,  # Parameters are defined in UserRegSerializer
    responses={
        201: OpenApiResponse(
            description="Успешная регистрация",
            response=UserRegSerializer,
            examples=[
                OpenApiExample(
                    "Пользователь успешно зарегистрирован",
                    value={
                        "message": "Пользователь успешно зарегистрирован",
                        "data": {
                            "email": "user@example.com",
                            "password": "new_user",
                            "username": "Cappucino",
                            "first_name": "string",
                            "last_name": "string",
                            "phone_number": "string"
                        }
                    }
                )
            ]
        ),
        422: OpenApiResponse(
            description="Ошибка валидации",
            response=UserRegSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка валидации", # Corrected key from 'valuse' to 'value'
                    value={
                        "message": "Неверные данные",
                        "errors": {
                            "email": [
                                "user with this email address already exists."
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
    request={'application/json': DeleteUserSerializer},
    examples=[
        OpenApiExample(
            "Удаление текущего пользователя",
            value={"id": 1},
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
                   Требуется аутентификация и права delete_user_data""",
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='ID пользователя',
            required=False
        ),
        OpenApiParameter(
            name='data_to_delete',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='поля, которые нужно удалить',
            required=False
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Данные удалены",
            response=DeleteUserDataSerializer,
            examples=[
                OpenApiExample(
                    "Успешный ответ",
                    value={"message": "Данные пользователя успешно удалены"}
                )
            ]
        ),
        400: OpenApiResponse(
            description="Ошибка валидации",
            response=DeleteUserDataSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"data_to_delete": ["Это поле обязательно."]}
                )
            ]
        ),
        401: OpenApiResponse(
            description="Не авторизован",
            response=DeleteUserDataSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"message": "Пользователь не аутентифицирован"}
                )
            ]
        ),
        403: OpenApiResponse(
            description="Нет прав",
            response=DeleteUserDataSerializer,
            examples=[
                OpenApiExample(
                    "Ошибка",
                    value={"message": "Недостаточно прав"}
                )
            ]
        ),
        404: OpenApiResponse(
            description="Пользователь не найден",
            response=DeleteUserDataSerializer,
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
            description='ID пользователя'
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Данные получены",
            response=GetUserDataSerializer, # Assuming UserRegSerializer is the response format
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
    description="Генерирует новый пароль и отправляет на email",
    request=RestorePasswordSerializer,  # 'email' expected in RestorePasswordSerializer
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