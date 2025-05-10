from django.db import models


ORDER_STATUS = (
        ('New', 'Новый'),
        ('Packed', 'Упакован'),  
        ('Shipped', 'Отправлен'),
        ('Completed', 'Завершен'),
        ('Canceled', 'Отменен'),
    )

class Order(models.Model):
    user = models.ForeignKey('Users.MarketUser', on_delete=models.CASCADE, related_name='orders')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_products')
    product = models.ForeignKey('Products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    buyer = models.ForeignKey('Users.MarketUser', on_delete=models.SET_NULL, null=True, related_name='order_products_buyer')
    seller = models.ForeignKey('Users.MarketUser', on_delete=models.SET_NULL, null=True, related_name='order_products_seller')
    status = models.CharField(max_length=255, choices=ORDER_STATUS, default='New')


class SellerOrder(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    seller = models.ForeignKey('Users.MarketUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

