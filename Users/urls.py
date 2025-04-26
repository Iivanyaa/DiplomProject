from django.urls import path
from . import views

urlpatterns = [
    path('BuyerRegister/', views.BuyerRegisterView.as_view(), name='BuyerRegister'),
    # path('SellerRegister/', views.SellerRegisterView.as_view(), name='SellerRegister'),
    path('login/', views.LoginView.as_view(), name='login'),
]