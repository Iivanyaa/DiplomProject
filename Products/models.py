from django.db import models
from Users.models import MarketUser
from easy_thumbnails.fields import ThumbnailerImageField


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
    Поле seller - продавец продукта
    """
    name = models.CharField(max_length=255, verbose_name="Название")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    description = models.TextField(blank=True, null=True, verbose_name="Описание") # Добавлено blank=True, null=True
    quantity = models.PositiveIntegerField(
        help_text="Количество продуктов в наличии у продавца",
        default=1,
        verbose_name="Количество"
    )
    is_available = models.BooleanField(
        default=True,
        help_text="Указывает, доступен ли продукт для покупки",
        verbose_name="Доступность"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
   
    seller = models.ForeignKey('Users.MarketUser', on_delete=models.CASCADE, null=True, related_name='products', verbose_name="Продавец")


    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        ordering = ['name']
        # Уникальность (name, seller) позволяет идентифицировать продукт для обновления
        # без поля SKU, которое отсутствует в вашей модели.
        unique_together = ('name', 'seller')


    def save(self, *args, **kwargs):
        """
        Переопределенный метод save, который при изменении quantity до 0
        изменяет is_available на False.
        """
        if self.quantity == 0:
            self.is_available = False
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Текстовое представление продукта.
        """
        seller_name = self.seller.username if self.seller else 'Неизвестный продавец'
        return f"{self.name} ({seller_name})"


class ProductImage(models.Model):
    """
    Модель для хранения изображений продукта.
    """
    # Связь с моделью Product
    product = models.ForeignKey(
        'Product', # Ссылка на модель 'Product' (в этом же приложении)
        related_name='images', # Название обратной связи для доступа к изображениям из объекта Product
        on_delete=models.CASCADE, # При удалении продукта удалять все его изображения
        help_text="Продукт, к которому относится изображение."
    )
    # Поле для хранения файла изображения, использующее easy-thumbnails
    image = ThumbnailerImageField(
        upload_to='product_images/', # Директория для загрузки изображений
        blank=True,
        null=True,
        help_text="Файл изображения продукта."
    )
    created_at = models.DateTimeField(auto_now_add=True) # Дата и время создания
    updated_at = models.DateTimeField(auto_now=True) # Дата и время последнего обновления

    class Meta:
        verbose_name = "Изображение продукта"
        verbose_name_plural = "Изображения продуктов"
        # Можно добавить дополнительные ограничения, например, уникальность, порядок и т.д.

    def __str__(self):
        # Строковое представление объекта, полезно для админ-панели
        return f"Изображение для {self.product.name} (ID: {self.id})"

    

# модель параметра продукта
class Parameters(models.Model):
    """
    Модель параметра продукта.
    Поле name - название параметра
    Поле value - значение параметра
    Поле product - продукт, к которому относится данный параметр
    """
    name = models.CharField(max_length=255, verbose_name="Название параметра")
    value = models.CharField(max_length=255, blank=True, null=True, verbose_name="Значение параметра")
    # Связь с моделью Product
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, related_name='parameters', verbose_name="Продукт")

    class Meta:
        verbose_name = "Параметр"
        verbose_name_plural = "Параметры"
        # Уникальность (name, product) для предотвращения дублирования параметров для одного продукта
        unique_together = ('name', 'product')

    def __str__(self):
        """
        Текстовое представление параметра.
        """
        return f"{self.name}: {self.value}"


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
    name = models.CharField(max_length=255, unique=True, verbose_name="Название категории")
    products = models.ManyToManyField(Product, related_name='categories', blank=True, verbose_name="Продукты")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']

    def __str__(self):
        """
        Текстовое представление категории.
        """
        return self.name
    

