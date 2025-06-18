from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import (
    extend_schema, 
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
    OpenApiResponse,
    OpenApiExample
)
from Orders.models import Order, OrderProduct
from Orders.serializers import OrderProductSerializer, OrderSearchSerializer, OrderStatusUpdateSerializer
from Users.models import MarketUser
from rest_framework import status
from Orders.schema import order_list_schema
from django.http import HttpResponse
from  rest_framework.decorators import api_view


@order_list_schema
class OrderView(APIView):
    # вьюшка для просмотра всех заказов текущего пользователя для Buyer и Seller либо по id
    def get(self, request, perm='Users.view_orders'):
        """
        Если передан id, то отображает заказ по id. 
        В противном случае получает список заказов для текущего пользователя в зависимости от его типа 
        пользователя и необязательных параметров поиска.

        Параметры:
        id (int): идентификатор заказа (опционально)

        Возвращает:
        Response: Объект Response, содержащий сообщение и список заказов, 
        сериализованных с помощью OrderProductSerializer, или сообщение об ошибке, 
        если у пользователя недостаточно прав или заказ не найден.
        """

        serializer = OrderSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        #проверяемие наличие прав у пользователя
        if not MarketUser.AccessCheck(self, request, perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # полчаем экземпляр пользователя
        user = MarketUser.objects.get(id=request.session.get('user_id'))
        orders_list = None
        # если не переданы данные, выводим список всех продуктов
        # Проверяем, что валидация данных не содержит никаких ключей
        if  serializer.validated_data == {} or serializer.validated_data == None:
            if user.user_type == 'Buyer':
                orders_list = user.order_products_buyer.all()
            if user.user_type == 'Seller':
                orders_list = user.order_products_seller.all()
            if user.user_type == 'Admin':
                orders_list = OrderProduct.objects.all()
            return Response({'message': 'Все заказы',
                             'orders': OrderProductSerializer(orders_list, many=True).data
                             }, status=status.HTTP_200_OK)
        # если переданы данные, выводим список заказов по id
        try:
            order_product = OrderProduct.objects.get(id=serializer.validated_data['id'])
        except OrderProduct.DoesNotExist:
            return Response({'message': 'Заказ не найден'}, status=status.HTTP_404_NOT_FOUND)
        if user.user_type == 'Buyer':
            orders_list = user.order_products_buyer.filter(**serializer.validated_data)
        if user.user_type == 'Seller':
            orders_list = user.order_products_seller.filter(**serializer.validated_data)
        if user.user_type == 'Admin':
            orders_list = OrderProduct.objects.filter(**serializer.validated_data)
        return Response({'message': 'Заказ найден',
                            'orders': OrderProductSerializer(orders_list, many=True).data
                            }, status=status.HTTP_200_OK)
    # вьюшка для изменения статуса заказа по id
    def put(self, request, perm='Users.update_order_status'):
        """
        Вьюшка для обновления статуса заказа по id.

        Параметры:
        id (int): идентификатор заказа
        status (str): новый статус заказа

        Возвращает:
        Ответ с сообщением и статусом заказа
        """
        serializer = OrderStatusUpdateSerializer(data=request.data)
        # проверяемие наличие прав у пользователя
        if not MarketUser.AccessCheck(self, request, perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # проверяем валидность входных данных
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # изменяем статус заказа
        order_product = OrderProduct.objects.get(id=serializer.validated_data['id'])
        if order_product.status == str(serializer.validated_data['status']):
            return Response({'message': 'Статус заказа не изменился'}, status=status.HTTP_400_BAD_REQUEST)
        order_product.status = str(serializer.validated_data['status'])
        order_product.save()
        if order_product.status == 'Canceled':
            order_product.product.quantity += order_product.quantity
            order_product.product.save()
            order_product.delete()
        return Response({'message': 'Статус заказа успешно изменен',
                         'order_product': order_product.id,
                         'status': order_product.status}, status=status.HTTP_200_OK)


@api_view(['GET'])
def trigger_error(request):
    result = 1 / 0
    return Response("This will never be seen.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

