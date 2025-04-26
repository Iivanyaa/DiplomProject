from django.urls import path
from . import views

urlpatterns = [
    path('BuyerRegister/', views.BuyerRegisterView.as_view(), name='BuyerRegister'),
    # path('SellerRegister/', views.SellerRegisterView.as_view(), name='SellerRegister'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('change_password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('delete_user/', views.DeleteUserView.as_view(), name='delete_user'),  
    path('update_user/', views.UpdateUserView.as_view(), name='update_user'),
    path('delete_user_data/', views.DeleteUserDataView.as_view(), name='delete_user_data'),
] 