from django.urls import path
from . import views

urlpatterns = [
    path(
        'profile/',
        views.SupplierProfileAPIView.as_view(),
        name='supplier-profile'
    ),
    path(
        'products/',
        views.SupplierProductListAPIView.as_view(),
        name='supplier-products'
    ),
    path(
        'orders/',
        views.SupplierOrderListAPIView.as_view(),
        name='supplier-orders'
    ),
]