from django.urls import path
from . import views

urlpatterns = [
    path(
        'register/',
        views.UserRegistrationAPIView.as_view(),
        name='user-register'
    ),
    path(
        'login/',
        views.CustomTokenObtainPairView.as_view(),
        name='token-obtain-pair'
    ),
    path(
        'password/reset/',
        views.PasswordResetAPIView.as_view(),
        name='password-reset'
    ),
]