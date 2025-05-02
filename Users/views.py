import os
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RestorePasswordSerializer, UserRegSerializer, DeleteUserDataSerializer, GetUserDataSerializer, LoginSerializer, ChangePasswordSerializer
from .models import MarketUser, UserGroup
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from .utils import generate_secure_password


# Регистрация покупателя по логину, почте и паролю
class UserRegisterView(APIView):
    """
    POST: Регистрация пользователя
    """
    def post(self, request):
        # Создаем объект serializer, передаем ему данные из запроса
        serializer = UserRegSerializer(data=request.data)
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
class LoginView(APIView):
    def post(self, request):
        # создаем объект serializer, передаем ему данные из запроса
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
class LogoutView(APIView):
    def post(self, request):
        # удаляем пользователя из сессии
        request.session.flush()
        # возвращаем ответ, что аутентификация прошла успешно
        return Response({'message': 'Успешный выход'}, status=status.HTTP_200_OK)
    

# Изменение пароля пользователя
class ChangePasswordView(APIView):
    def post(self, request):
        # Получаем текущего пользователя из сессии
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
class DeleteUserView(APIView):
    def delete(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
            # Если пользователь не аутентифицирован, возвращаем ошибку
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED, content_type='application/json')
        try:
            user = MarketUser.objects.get(id=user_id)
        except MarketUser.DoesNotExist:
            return Response({'message': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND, content_type='application/json')
        if not user.has_perm("Users.delete_user"):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN, content_type='application/json')
        # Удаляем пользователя
        user.delete()
        # Возвращаем ответ, что пользователь успешно удален
        return Response({'message': 'Пользователь успешно удален'}, status=status.HTTP_200_OK, content_type='application/json')


# Изменение данных пользователя
class UpdateUserView(APIView):
    def put(self, request):
        # ID текущего пользователя
        user_id = request.session.get('user_id')
        if not user_id:
            # Если пользователь не аутентифицирован, возвращаем ошибку
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
        # Получаем объект пользователя по ID
        try:
            user = MarketUser.objects.get(id=user_id)
        except:
            return Response({'message': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)    
        # Создаем объект serializer, передаем ему данные из запроса и объект пользователя
        if not user.has_perm("Users.update_user"):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN, content_type='application/json')
        serializer = UserRegSerializer(user, data=request.data, partial=True)
        # Проверяем, валидны ли данные
        if serializer.is_valid(raise_exception=True):
            # Если данные валидны, сохраняем их
            serializer.save()
            # Возвращаем ответ, что данные успешно изменены
            return Response(serializer.data, status=status.HTTP_200_OK)
        # Если данные не валидны, возвращаем ошибки
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# удаление данных пользователя
class DeleteUserDataView(APIView):
    def delete(self, request):
        # ID текущего пользователя
        user_id = request.session.get('user_id')
        if not user_id:
            # Если пользователь не аутентифицирован, возвращаем ошибку
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
        # Получаем объект пользователя по ID
        user = MarketUser.objects.get(id=user_id)
        # Проверяем, имеет ли пользователь право на удаление данных
        if not user.has_perm("Users.delete_user_data"):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN, content_type='application/json')
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
class GetUserDataView(APIView):
    def get(self, request):
        # Получаем ID текущего пользователя из сессии
        user_id = request.session.get('user_id')
        if not user_id:
            # Если пользователь не аутентифицирован, возвращаем ошибку
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
        # Проверяем, имеет ли пользователь право на получение данных
        user = MarketUser.objects.get(id=user_id)
        if not user.has_perm("Users.get_user_data"):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN, content_type='application/json')
        # Создаем объект сериализатора, передаем ему данные из запроса
        serializer = GetUserDataSerializer(data=request.data)
        # Проверяем, валидны ли данные
        if serializer.is_valid(raise_exception=True):
            # Получаем объект пользователя по ID, указанному в сериализаторе
            user = MarketUser.objects.get(id=serializer.validated_data['user_id'])
            # Возвращаем данные пользователя
            return Response({
                'message': 'Данные пользователя успешно получены',
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phone_number,
                'email': user.email,
                'username': user.username
            }, status=status.HTTP_200_OK)
        # Если данные не валидны, возвращаем ошибку
        return Response({'message': 'Данные невалидны'}, status=status.HTTP_400_BAD_REQUEST)


# восстановление пароля по электроронному адресу
class RestorePasswordView(APIView):
    def post(self, request):
        # Создаем объект сериализатора, передаем ему данные из запроса
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

