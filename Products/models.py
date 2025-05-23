from django.db import models
from Users.models import MarketUser


# модель продукта
class Product(models.Model):
    """
    Модель продукта. 
    Поле name - название продукта
    Поле price - цена продукта
    Поле description - описание продукта
    Поле quantity - количество продукта
    Поле is_available - доступен ли продукт
    Поле created_at - дата создания
    Поле updated_at - дата обновления
    Поле parameters - параметры продукта
    """
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    quantity = models.PositiveIntegerField()
    is_available = models.BooleanField(
        default=True,
        help_text="Указывает, доступен ли продукт для покупки",
        auto_created=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    seller = models.ForeignKey('Users.MarketUser', on_delete=models.CASCADE, null=True, related_name='products')

    def save(self, *args, **kwargs):
        """
        переопределенный метод save, который при изменении quantity до 0
        изменяет is_available на False
        """
        if self.quantity == 0:
            self.is_available = False
        super().save(*args, **kwargs)

    def __str__(self):
        """
        текстовое представление продукта
        """
        return self.name
    

# модель параметра продукта
class Parameters(models.Model):
    """
    Модель параметра продукта. 
    Поле name - название параметра
    Поле value - значение параметра
    Поле products - продукты, у которых есть данный параметр
    """
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, null=True, related_name='parameters')

    def __str__(self):
        """
        текстовое представление параметра
        """
        return self.name    


# модель корзины
class Cart(models.Model):
    """
    Модель корзины. 
    Поле user - пользователь, которому принадлежит корзина
    Поле products - продукты в корзине
    Поле created_at - дата создания
    Поле updated_at - дата обновления
    """
    # unique=True - означает, что для каждого пользователя может быть только одна корзина.
    # Если создать для пользователя еще одну корзину, то предыдущая будет удалена.
    user = models.ForeignKey('Users.MarketUser', on_delete=models.SET_NULL, null=True, related_name='carts', unique=True)
    products = models.ManyToManyField(Product, related_name='carts', through='CartProduct')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def TotalPrice(self):
        """
        общая стоимость корзины
        """
        return sum([product.price*product.cart_products.get(cart=self).quantity for product in self.products.all()])


# модель продукта в корзине
class CartProduct(models.Model):
    """
    Модель продукта в корзине. 
    Поле cart - корзина, в которой находится продукт
    Поле product - продукт в корзине
    Поле quantity - количество продукта в корзине
    Поле created_at - дата создания
    Поле updated_at - дата обновления
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_products')
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# модель категории продуктов
class Category(models.Model):
    """
    Модель категории продуктов. 
    Поле name - название категории
    Поле products - продукты в категории
    """
    name = models.CharField(max_length=255)
    products = models.ManyToManyField(Product, related_name='categories', blank=True)

    def __str__(self):
        """
        текстовое представление категории
        """
        return self.name
    

