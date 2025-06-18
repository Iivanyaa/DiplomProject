from django.urls import path
from . import views

urlpatterns = [
    path('Orders/', views.OrderView.as_view(), name='Orders'),
    path('rollbar_debug/', views.trigger_error, name='rollbar_debug'),
] 
