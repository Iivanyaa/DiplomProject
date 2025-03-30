from rest_framework import serializers
from .models import Supplier, SupplierProduct
from apps.users.serializers import UserSerializer

class SupplierSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    is_accepting_orders = serializers.BooleanField(read_only=True)

    class Meta:
        model = Supplier
        fields = [
            'user', 
            'company_name', 
            'address', 
            'tax_id',
            'is_accepting_orders',
            'created_at'
        ]

class SupplierProductSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField()
    
    class Meta:
        model = SupplierProduct
        fields = [
            'id',
            'product',
            'quantity_available',
            'last_updated'
        ]

class SupplierOrderSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    include_details = serializers.BooleanField(default=False)