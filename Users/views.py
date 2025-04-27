from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserRegSerializer, DeleteUserDataSerializer, GetUserDataSerializer, LoginSerializer, ChangePasswordSerializer
from .models import MarketUser
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password, check_password


# Регистрация покупателя по логину, почте и паролю
class BuyerRegisterView(APIView):
    def post(self, request):
        # Создаем объект serializer, передаем ему данные из запроса
        serializer = UserRegSerializer(data=request.data)
        # Проверяем, валидны ли данные
        if serializer.is_valid():
            # Если данные валидны, сохраняем их
            serializer.save()
            # Возвращаем данные и статус 201 CREATED
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # Если данные не валидны, возвращаем ошибки и статус 400 BAD REQUEST
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
                # сохраняем пользователя в сессии
                request.session['user_id'] = user.id
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
        # ID текущего пользователя
        user_id = request.session.get('user_id')
        if not user_id:
            # Если пользователь не аутентифицирован, возвращаем ошибку
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
        # Удаляем пользователя
        MarketUser.objects.filter(id=user_id).delete()
        # Возвращаем ответ, что пользователь успешно удален
        return Response({'message': 'Пользователь успешно удален'}, status=status.HTTP_200_OK)


# Изменение данных пользователя
class UpdateUserView(APIView):
    def put(self, request):
        # ID текущего пользователя
        user_id = request.session.get('user_id')
        if not user_id:
            # Если пользователь не аутентифицирован, возвращаем ошибку
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
        # Получаем объект пользователя по ID
        user = MarketUser.objects.get(id=user_id)
        # Создаем объект serializer, передаем ему данные из запроса и объект пользователя
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
        current_user_id = request.session.get('user_id')
        if not current_user_id:
            # Если пользователь не аутентифицирован, возвращаем ошибку
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
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


        