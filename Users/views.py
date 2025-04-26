from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import BuyerRegSerializer, LoginSerializer
from .models import Buyer
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password, check_password


# Регистрация покупателя по логину, почте и паролю
class BuyerRegisterView(APIView):
    def post(self, request):
        # Создаем объект serializer, передаем ему данные из запроса
        serializer = BuyerRegSerializer(data=request.data)
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
                # возвращаем ответ, что аутентификация прошла успешно
                return Response({'message': 'Успешная аутентификация'}, status=status.HTTP_200_OK)
        # если аутентификация прошла неудачно
        return Response({'message': 'неверные данные'}, status=status.HTTP_400_BAD_REQUEST)

