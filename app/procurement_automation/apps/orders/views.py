from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .serializers import OrderSerializer, OrderItemSerializer
from apps.orders.models import Order, OrderItem
from .models import Order, OrderItem
from .serializers import (
    OrderSerializer,
    OrderItemSerializer,
    OrderConfirmationSerializer
)
from apps.core.tasks import send_email_task


class OrderListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)\
            .prefetch_related('items__product')\
            .order_by('-created_at')

class OrderDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class OrderConfirmationAPIView(generics.GenericAPIView):
    serializer_class = OrderConfirmationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        order = generics.get_object_or_404(
            Order,
            pk=pk,
            user=request.user,
            status='new'
        )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Обновление заказа
        order.delivery_address = serializer.validated_data['delivery_address']
        order.status = 'processing'
        order.save()

        # Отправка email через Celery
        send_email_task.delay(
            subject="Order Confirmation",
            template_name="emails/order_confirmation.html",
            context={
                'order_id': order.id,
                'total': order.total,
                'delivery_address': order.delivery_address
            },
            recipient_list=[request.user.email]
        )

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_200_OK
        )

class CartAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderItemSerializer

    def get(self, request):
        order, _ = Order.objects.get_or_create(
            user=request.user,
            status='new'
        )
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def post(self, request):
        order, created = Order.objects.get_or_create(
            user=request.user,
            status='new'
        )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        product = serializer.validated_data['product']
        if product.stock < serializer.validated_data['quantity']:
            return Response(
                {'error': 'Insufficient stock'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=serializer.validated_data['quantity'],
            price=product.price
        )
        
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )