from django.contrib import admin

from .models import Product, Category, Cart, CartProduct

admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Cart)
admin.site.register(CartProduct)

# Register your models here.
