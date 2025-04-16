from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.CartAPIView.as_view(), name='cart'),
    path(
        'orders/',
        views.OrderListCreateAPIView.as_view(),
        name='order-list'
    ),
    path(
        'orders/<int:pk>/',
        views.OrderDetailAPIView.as_view(),
        name='order-detail'
    ),
    path(
        'orders/<int:pk>/confirm/',
        views.OrderConfirmationAPIView.as_view(),
        name='order-confirm'
    ),
]