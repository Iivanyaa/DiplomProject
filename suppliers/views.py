from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Supplier, SupplierProduct
from .serializers import (
    SupplierSerializer,
    SupplierProductSerializer,
    SupplierOrderSerializer
)

class SupplierProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.supplier_profile

class SupplierProductListAPIView(generics.ListAPIView):
    serializer_class = SupplierProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SupplierProduct.objects.filter(
            supplier=self.request.user.supplier_profile
        ).select_related('product')

class SupplierOrderListAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SupplierOrderSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Здесь реализация получения заказов поставщика
        # с фильтрацией по датам и детализации
        return Response(
            {"message": "Orders retrieved successfully"},
            status=status.HTTP_200_OK
        )