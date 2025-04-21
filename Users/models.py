from django.db import models
from django.contrib.auth.models import AbstractUser
from Goods.models import Product

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

class Buyer(User):
    cart = models.OneToOneField('Cart', on_delete=models.CASCADE, blank=True, null=True)
    contacts = models.OneToOneField('Contact', on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        verbose_name = 'Покупатель'
        verbose_name_plural = 'Покупатели'

class Seller(User):
    company_name = models.CharField(max_length=255, blank=True, null=True)
    company_address = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = 'Продавец'
        verbose_name_plural = 'Продавцы'

class Cart(models.Model):
    buyer = models.OneToOneField(Buyer, on_delete=models.CASCADE, blank=True, null=True)
    products = models.ManyToManyField('Product', through='CartItem', related_name='carts')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

class Contact(models.Model):
    buyer = models.OneToOneField(Buyer, on_delete=models.CASCADE, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True) #Нужно добавить ограничение на количество адресов (5)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    class Meta:
        verbose_name = 'Позиция в корзине'
        verbose_name_plural = 'Позиции в корзине'
