from django.db import models
from apps.users.models import User

class Supplier(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='supplier_profile'
    )
    company_name = models.CharField(max_length=255)
    address = models.TextField()
    tax_id = models.CharField(max_length=50, unique=True)
    is_accepting_orders = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} ({self.user.email})"

class SupplierProduct(models.Model):
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='supplier_products'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='supplier_products'
    )
    quantity_available = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('supplier', 'product')

    def __str__(self):
        return f"{self.product.name} - {self.supplier.company_name}"