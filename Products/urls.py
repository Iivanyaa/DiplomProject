from django.urls import path
from . import views

urlpatterns = [
    path('Products/', views.ProductsView.as_view(), name='Products'),
    path('Categories/', views.CategoriesView.as_view(), name='Categories'),
] 
