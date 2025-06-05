from django.urls import path
from . import views

urlpatterns = [
    path('Products/', views.ProductsView.as_view(), name='Products'),
    path('Products/Change/', views.ProductsChangeView.as_view(), name='ChangeProducts'),
    path('Categories/', views.CategoriesView.as_view(), name='Categories'),
    path('Cart/', views.CartView.as_view(), name='Cart')
] 
