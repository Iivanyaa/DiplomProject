from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from Orders.models import Order, OrderProduct
from Orders.serializers import OrderProductSerializer, OrderSearchSerializer, OrderStatusUpdateSerializer
from Users.models import MarketUser
from rest_framework import status

class OrderView(APIView):
    # вьюшка для просмотра всех заказов текущего пользователя для Buyer и Seller либо по id
    def get(self, request, perm='Users.view_orders'):
        serializer = OrderSearchSerializer(data=request.data)
        #проверяемие наличие прав у пользователя
        if not MarketUser.AccessCheck(self, request, perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # проверяем валидность входных данных
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # полчаем экземпляр пользователя
        user = MarketUser.objects.get(id=request.session.get('user_id'))
        print(user.user_type)
        orders_list = None
        # если не переданы данные, выводим список всех продуктов
        if serializer.validated_data.keys() == set():
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
        else:
            if user.user_type == 'Buyer':
                orders_list = user.order_products_buyer.filter(**serializer.validated_data)
            if user.user_type == 'Seller':
                orders_list = user.order_products_seller.filter(**serializer.validated_data)
            if user.user_type == 'Admin':
                orders_list = OrderProduct.objects.filter(**serializer.validated_data)
            if not orders_list.exists():
                return Response({'message': 'Заказы не найдены'}, status=status.HTTP_404_NOT_FOUND)
            return Response({'message': 'Заказы найдены',
                             'orders': OrderProductSerializer(orders_list, many=True).data
                             }, status=status.HTTP_200_OK)
    
    # вьюшка для изменения статуса заказа по id
    def put(self, request, perm='Users.update_order_status'):
        serializer = OrderStatusUpdateSerializer(data=request.data)
        # проверяемие наличие прав у пользователя
        if not MarketUser.AccessCheck(self, request, perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # проверяем валидность входных данных
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # изменяем статус заказа
        order = OrderProduct.objects.get(id=serializer.validated_data['id'])
        if order.status == str(serializer.validated_data['status']):
            return Response({'message': 'Статус заказа не изменился'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = str(serializer.validated_data['status'])
        order.save()
        if order.status == 'Canceled':
            for order_product in order.order.order_products.all():
                order_product.product.quantity += order_product.quantity
                order_product.product.save()
                order_product.delete()
        return Response({'message': 'Статус заказа успешно изменен',
                         'order': order.id,
                         'status': order.status}, status=status.HTTP_200_OK)

    
    
    
    # def get(self, request):
    #     if 'id' in request.data:
    #         order = Order.objects.get(id=request.data['id'])
    #         if order.buyer.id == request.session.get('user_id'):
    #             return Response({'message': 'Заказ найден',
    #                              'order': OrderSerializer(order).data
    #                              }, status=status.HTTP_200_OK)
    #         else:
    #             return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
    #     else:
    #         orders = Order.objects.filter(buyer__id=request.session.get('user_id'))
    #         return Response({'message': 'Все заказы',
    #                          'orders': OrderSerializer(orders, many=True).data
    #                          }, status=status.HTTP_200_OK)
    
