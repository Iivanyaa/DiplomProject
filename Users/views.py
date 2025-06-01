import os
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter, OpenApiTypes
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import DeleteUserSerializer, RestorePasswordSerializer, UserRegSerializer, DeleteUserDataSerializer, GetUserDataSerializer, LoginSerializer, ChangePasswordSerializer, UserUpdateSerializer
from .models import MarketUser, UserGroup
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from .utils import generate_secure_password
from .schema import *


# Регистрация покупателя по логину, почте и паролю
@user_register_schema
class UserRegisterView(APIView):
    def post(self, request):
        # Создаем объект serializer, передаем ему данные из запроса
        """
        POST-запрос на регистрацию пользователя.

        Параметры:
        request (Request): объект запроса Django

        Возвращает:
        Response: объект ответа с созданным пользователем, если данные валидны,
            или сообщение об ошибке, если данные не валидны.
        """

        serializer_reg = UserRegSerializer(data=request.data)
        # Проверяем, валидны ли данные
        if serializer.is_valid():
            # если данные валидны, то создаем пользователя
            user = serializer.save()
            # Добавляем пользователя в группу, которая соответствует типу пользователя
            user_type = serializer.validated_data.get('user_type', 'Buyer')
            UserGroup.objects.get(name=user_type).user_set.add(user)
            # возвращаем ответ
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # если данные не валидны, то возвращаем ошибки
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# логин пользователя
@user_login_schema
class LoginView(APIView):
    def post(self, request):
        # создаем объект serializer, передаем ему данные из запроса
        """
        POST-запрос на аутентификацию пользователя.

        Параметры:
        request (Request): объект запроса Django

        Возвращает:
        Response: объект ответа с сообщением об успешной аутентификации,
            если данные валидны и аутентификация прошла успешно,
            или сообщение об ошибке, если данные не валидны
            или аутентификация прошла неудачно.
        """
        serializer = LoginSerializer(data=request.data)
        # если объект serializer валидный, то
        if serializer.is_valid(raise_exception=True):
            # пытаемся аутентифицировать пользователя
            user = authenticate(**serializer.validated_data)
            # если аутентификация прошла успешно
            if user:
                # сохраняем все данные пользователя в сессии
                request.session['user_id'] = user.id
                request.session['username'] = user.username
                # возвращаем ответ, что аутентификация прошла успешно
                return Response({'message': 'Успешная аутентификация'}, status=status.HTTP_200_OK)
        # если аутентификация прошла неудачно
        return Response({'message': 'неверные данные'}, status=status.HTTP_400_BAD_REQUEST)

# выход пользователя из системы
@user_logout_schema
class LogoutView(APIView):
    def post(self, request):
        # удаляем пользователя из сессии
        """
        POST-запрос на выход пользователя из системы.

        Параметры:
        request (Request): объект запроса Django

        Возвращает:
        Response: объект ответа с сообщением об успешном выходе,
            если пользователь аутентифицирован,
            или сообщение об ошибке, если пользователь не аутентифицирован
        """
        request.session.flush()
        # возвращаем ответ, что аутентификация прошла успешно
        return Response({'message': 'Успешный выход'}, status=status.HTTP_200_OK)

# Изменение пароля пользователя
@user_change_password_schema
class ChangePasswordView(APIView):
    def post(self, request):
        # Получаем текущего пользователя из сессии
        """
        POST-запрос на изменение пароля пользователя.

        Параметры:
        request (Request): объект запроса Django

        Возвращает:
        Response: объект ответа с сообщением об успешном изменении пароля,
            если пользователь аутентифицирован и имеет необходимые права,
            или сообщение об ошибке, если пользователь не аутентифицирован,
            не имеет прав, старый пароль неверный, или новый пароль совпадает
            со старым. Также возвращает ошибки, если данные не валидны.
        """

        user_id = request.session.get('user_id')
        if not user_id:
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
        # Получаем объект пользователя по ID
        user = MarketUser.objects.get(id=user_id)
        # Проверяем, имеет ли пользователь право на изменение пароля
        if not user.has_perm('Users.change_password'):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # Создаем объект serializer, передаем ему данные из запроса
        serializer = ChangePasswordSerializer(data=request.data)
        # Проверяем, валидны ли данные
        if serializer.is_valid(raise_exception=True):
            # Если данные валидны, проверяем старый пароль
            if not check_password(serializer.validated_data['old_password'], user.password):
                return Response({'message': 'Неверный старый пароль'}, status=status.HTTP_400_BAD_REQUEST)
            # Если старый пароль верный, проверяем новый пароль
            if serializer.validated_data['old_password'] == serializer.validated_data['new_password']:
                return Response({'message': 'Новый пароль не может совпадать со старым'}, status=status.HTTP_400_BAD_REQUEST)
            # Обновляем пароль
            user.password = make_password(serializer.validated_data['new_password'])
            user.save()
            # Возвращаем ответ, что пароль успешно изменен
            return Response({'message': 'Пароль успешно изменен'}, status=status.HTTP_200_OK)
        # Если данные не валидны, возвращаем ошибки
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# Удаление пользователя
@delete_user_schema
class DeleteUserView(APIView):
    def delete(self, request):
        # создаем объект serializer, передаем ему данные из запроса
        """
        DELETE-запрос на удаление пользователя.

        Параметры:
        request (Request): объект запроса Django

        Возвращает:
        Response: объект ответа с сообщением об успешном удалении
            пользователя, если пользователь имеет необходимые права, или
            сообщение об ошибке, если таких прав нет.
        """
        serializer = DeleteUserSerializer(data=request.data)
        # проверяем, есть ли в запросе id пользователя или username
        if 'id' not in request.data and 'username' not in request.data:
            # если нет, то удаляем текущего пользователя
            # Проверяем, имеет ли пользователь право на самоудаление
            if not MarketUser.AccessCheck(self, request=request, perm='Users.delete_self'):
                return Response({'message': 'Недостаточно прав'}, status=status.HTTP_401_UNAUTHORIZED, content_type='application/json')
            # получаем объеат пользователя из сессии
            user = MarketUser.objects.get(id=request.session.get('user_id'))
            # Удаляем пользователя
            user.delete()
            # Возвращаем ответ, что пользователь успешно удален
            return Response({'message': 'Пользователь успешно удален'}, status=status.HTTP_200_OK, content_type='application/json')
        # если в запросе есть id пользователя или username, то удаляем пользователя по id или username
        # Проверяем, имеет ли пользователь право на удаление пользователя
        if not MarketUser.AccessCheck(self, request=request, perm='Users.delete_user'):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_401_UNAUTHORIZED, content_type='application/json')
        # удаляем пользователя по id или username
        if serializer.is_valid(raise_exception=True):
            user = MarketUser.objects.filter(**serializer.validated_data).first()
            user.delete()
        # Возвращаем ответ, что пользователь успешно удален
        return Response({'message': 'Пользователь успешно удален'}, status=status.HTTP_200_OK, content_type='application/json')


# Изменение данных пользователя
@update_user_data_schema
class UpdateUserView(APIView):
    def put(self, request, perm='Users.update_user'):
        """
        PUT-запрос на изменение данных пользователя.

        Параметры:
        request (Request): объект запроса Django

        Возвращает:
        Response: объект ответа с обновленными данными
            пользователя, если пользователь аутентифицирован и
            имеет необходимые права, или сообщение об ошибке,
            если пользователь не аутентифицирован, не имеет
            прав, или ID пользователя не найден.
        """
        serializer = UserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # проверяем аутентифицирован ли пользователь
        if request.session.get('user_id') is None:
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
        # Получаем ID пользователя из запроса или из сессии
        user_id = serializer.validated_data.get('id') or request.session.get('user_id')
        if not user_id:
            return Response({'message': 'ID пользователя не найден'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Получаем пользователя по ID
        user = MarketUser.objects.filter(id=user_id).first()
        if not user:
            return Response({'message': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)
        
        # Проверяем наличие прав на изменение данных пользователя
        if user_id != request.session.get('user_id') and not MarketUser.AccessCheck(self, request=request, perm=perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        
        # Обновляем данные пользователя
        for field, value in serializer.validated_data.items():
            setattr(user, field, value)
        user.save()
        
        return Response(serializer.data, status=status.HTTP_200_OK)


# удаление данных пользователя
@delete_user_data_schema
class DeleteUserDataView(APIView):
    def delete(self, request, perm='Users.delete_user_data'):
        # проверяем аутентифицирован ли пользователь
        """
        Удаляет выбранные данные пользователя на основе предоставленных данных.

        Параметры:
        request (Request): объект запроса Django
        perm (str): требуемое разрешение для удаления данных пользователя

        Возвращает:
        Response: объект ответа с сообщением об успешном удалении данных, если
            пользователь аутентифицирован, имеет необходимые права и данные
            пользователя существуют. В противном случае возвращает сообщение
            об ошибке, если пользователь не аутентифицирован, не имеет прав,
            или данные пользователя не найдены.
        """

        if request.session.get('user_id') is None:
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
        # Получаем ID пользователя из запроса, если он не указан, то используем ID из сессии
        user_id = request.data.get('id') or request.session.get('user_id')
        # проверяем наличие пользователя
        if not MarketUser.objects.filter(id=user_id).exists():
            return Response({'message': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)
        # Проверяем наличия прав на удаление данных пользователя
        if user_id != request.session.get('user_id') and not MarketUser.AccessCheck(self, request=request, perm=perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_401_UNAUTHORIZED)
        # Получаем объект пользователя по ID
        user = MarketUser.objects.get(id=user_id)
        # Создаем объект serializer, передаем ему данные из запроса
        serializer = DeleteUserDataSerializer(data=request.data)
        # удаляем выбранные параметры пользователя в соответствии с данными сериализатора
        if serializer.is_valid(raise_exception=True):
            # Если данные валидны, удаляем указанные поля
            for field in serializer.validated_data['data_to_delete']:
                # Проверяем, существует ли поле у пользователя
                if hasattr(user, field):
                    # Удаляем поле
                    setattr(user, field, None)
                    user.save()
            
        # Возвращаем ответ, что данные успешно удалены
            return Response({'message': 'Данные пользователя успешно удалены'}, status=status.HTTP_200_OK)
        # Если данные не валидны, возвращаем ошибки
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# получение данных пользователя по ID
@get_user_data_schema
class GetUserDataView(APIView):
    def get(self, request, perm='Users.get_user_data'):
        # Создаем объект сериализатора, передаем ему данные из запроса
        """
        GET-запрос на получение данных пользователя.

        Параметры:
        request (Request): объект запроса Django
        perm (str): требуемое разрешение для получения данных пользователя

        Возвращает:
        Response: объект ответа с данными пользователя, если пользователь
            аутентифицирован, имеет необходимые права и пользователь
            существует. В противном случае возвращает сообщение об ошибке,
            если пользователь не аутентифицирован, не имеет прав, или
            пользователь не найден.
        """
        print(request.query_params)
        serializer = GetUserDataSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        print(serializer.validated_data)
        print(serializer.is_valid())
        # получаем ID пользователя из запроса, если он не указан, то используем ID из сессии
        user_id = serializer.validated_data.get('id') or request.session.get('user_id')
        print(user_id, request.session.get('user_id'))
        print(request.session.get('user_id'))
        print(request.session)
        # проверяем наличия прав на получение данных другого пользователя
        if request.session.get('user_id') is None or user_id != request.session.get('user_id') and not MarketUser.AccessCheck(self, request=request, perm=perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_401_UNAUTHORIZED , content_type='application/json')
        # проверяем наличие пользователя
        if not MarketUser.objects.filter(id=user_id).exists():
            return Response({'message': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

        # Получаем объект пользователя по ID
        user = MarketUser.objects.get(id=user_id)
        
        # Возвращаем данные пользователя
        return Response({
            'message': 'Данные пользователя успешно получены',
            'данные пользователя':UserRegSerializer(user).data
        }, status=status.HTTP_200_OK)


# восстановление пароля по электроронному адресу
@restore_password_schema
class RestorePasswordView(APIView):
    def post(self, request):
        # Создаем объект сериализатора, передаем ему данные из запроса
        """
        POST-запрос на восстановление пароля пользователя по его электронному адресу.

        Параметры:
        request (Request): объект запроса Django, содержащий электронный адрес пользователя.

        Возвращает:
        Response: объект ответа с сообщением об успешном изменении пароля, если
            пользователь с указанным электронным адресом существует. В противном
            случае возвращает сообщение об ошибке, если пользователь не найден.
        """

        serializer = RestorePasswordSerializer(data=request.data)
        # Проверяем, валидны ли данные
        if serializer.is_valid(raise_exception=True):
            # Получаем объект пользователя по электронному адресу
            try:
                user = MarketUser.objects.get(email=serializer.validated_data['email'])
            except MarketUser.DoesNotExist:
                return Response({'message': 'Пользователь с таким электронным адресом не найден'}, status=status.HTTP_404_NOT_FOUND)
            #Генерируем новый пароль
            new_password = generate_secure_password()
            # Обновляем пароль пользователя
            user.password = make_password(new_password)
            user.save()
            # Отправляем письмо с новым паролем
            send_mail(
                subject='Восстановление пароля',
                from_email=os.getenv('EMAIL_HOST_USER'),
                message=f'Ваш новый пароль: {new_password}',
                recipient_list=[user.email],
                fail_silently=False,
            )
            # Возвращаем ответ, что пароль успешно изменен
            return Response({'message': 'Пароль успешно изменен'}, status=status.HTTP_200_OK)

