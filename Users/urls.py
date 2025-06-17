from django.urls import path
from . import views

urlpatterns = [
    path('BuyerRegister/', views.UserRegisterView.as_view(), name='BuyerRegister'),
    # path('SellerRegister/', views.SellerRegisterView.as_view(), name='SellerRegister'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('change_password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('delete_user/', views.DeleteUserView.as_view(), name='delete_user'),  
    path('update_user/', views.UpdateUserView.as_view(), name='update_user'),
    path('delete_user_data/', views.DeleteUserDataView.as_view(), name='delete_user_data'),
    path('Users/', views.GetUserDataView.as_view(), name='Get_User'),
    path('restore_password/', views.RestorePasswordView.as_view(), name='restore_password'),
    path('Users/Contacts/', views.AddContactView.as_view(), name='contacts'),
    path('login/social/', SocialAuthView.as_view(), name='social_auth'),
] 