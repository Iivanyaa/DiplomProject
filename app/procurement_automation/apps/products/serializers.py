from rest_framework import serializers
from ..models import Product, ProductCategory

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'description']

class ProductSerializer(serializers.ModelSerializer):
    category = ProductCategorySerializer()
    supplier = serializers.StringRelatedField()
    
    class Meta:
        model = Product
        fields = [
            'id', 
            'name', 
            'supplier', 
            'category', 
            'price', 
            'characteristics',
            'stock',
            'is_active'
        ]
        read_only_fields = ['supplier']