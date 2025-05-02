# utils/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.exceptions import PermissionDenied, NotAuthenticated

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, PermissionDenied):
        response.data = {
            'message': 'Доступ запрещен. Недостаточно прав.',
            'status_code': 403  # Или другой код
        }
        # response.status_code = 400  # Для изменения статуса

    elif isinstance(exc, NotAuthenticated):
        response.data = {
            'message': 'Требуется аутентификация.',
            'status_code': 401
        }

    return response