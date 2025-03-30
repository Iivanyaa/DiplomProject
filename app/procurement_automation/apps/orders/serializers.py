from rest_framework import serializers
from .models import Order, OrderItem
from apps.products.serializers import ProductSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'quantity',
            'price',
            'total'
        ]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status = serializers.CharField(read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'status',
            'total',
            'delivery_address',
            'created_at',
            'updated_at',
            'items'
        ]

class OrderConfirmationSerializer(serializers.Serializer):
    delivery_address = serializers.CharField(
        required=True,
        max_length=500
    )
    agree_terms = serializers.BooleanField(required=True)

    def validate_agree_terms(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must agree to the terms and conditions"
            )
        return value