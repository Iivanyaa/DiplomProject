from django.db import models
from django.contrib.auth.models import Group, Permission, AnonymousUser, User
from Goods.models import Product


class MarketUser(User):
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    pass

# создаем моедль группы покупателей
class BuyerGroup(Group):
    class Meta:
        verbose_name = 'Покупатель'
        verbose_name_plural = 'Покупатели'

# создаем модель группы продавцов
class SellerGroup(Group):
    class Meta:
        verbose_name = 'Продавец'
        verbose_name_plural = 'Продавцы'

# создаем модель группы администраторов
class AdminGroup(Group):
    class Meta:
        verbose_name = 'Администратор'
        verbose_name_plural = 'Администраторы'






# class Seller(UnauthorizedUser):
#     company_name = models.CharField(max_length=255, blank=True, null=True)
#     company_address = models.CharField(max_length=255, blank=True, null=True)
#     # ManyToManyField для связи с продуктами, которые доступны у продавца
#     # Available_products = models.ManyToManyField(Product.objects.filter(Availiable=True), blank=True, related_name='sellers')

#     class Meta:
#         verbose_name = 'Продавец'
#         verbose_name_plural = 'Продавцы'

# class Cart(models.Model):
#     buyer = models.OneToOneField(Buyer, on_delete=models.CASCADE, blank=True, null=True, related_name='cart')
#     # products = models.ManyToManyField('Product', through='CartItem', related_name='carts')
#     total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

#     class Meta:
#         verbose_name = 'Корзина'
#         verbose_name_plural = 'Корзины'

# class Contact(models.Model):
#     buyer = models.OneToOneField(Buyer, on_delete=models.CASCADE, blank=True, null=True, related_name='contact')
#     address = models.CharField(max_length=255, blank=True, null=True) #Нужно добавить ограничение на количество адресов (5)
#     phone_number = models.CharField(max_length=20, blank=True, null=True)
#     email = models.EmailField(blank=True, null=True)

#     class Meta:
#         verbose_name = 'Контакт'
#         verbose_name_plural = 'Контакты'


# class CartItem(models.Model):
#     cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     quantity = models.IntegerField(default=1)

#     class Meta:
#         verbose_name = 'Позиция в корзине'
#         verbose_name_plural = 'Позиции в корзине'
