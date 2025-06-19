from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import UserGroup


@receiver(post_migrate)
def create_initial_groups(sender, **kwargs):
    # создаем 3 группы: администратор, продавец, покупатель
    admin_group, created = UserGroup.objects.get_or_create(name='Admin')  # администратор
    seller_group, created = UserGroup.objects.get_or_create(name='Seller')  # продавец
    buyer_group, created = UserGroup.objects.get_or_create(name='Buyer')  # покупатель

    admin_group.permissions.clear()
    seller_group.permissions.clear()
    buyer_group.permissions.clear()

    # создаем права
    # права администратора
    admin_permissions = [   'add_user', 'change_user', 'delete_user',
                            'view_user', 'update_user', 'delete_user_data',
                            'get_user_data', 'change_password', 'delete_product',
                            'create_category', 'delete_category', 'update_category',
                            'get_category', 'view_orders', 'update_order_status', 'delete_self',
                            'add_product_image', 'change_product_image', 'delete_product_image',
                            ]
    # права продавца
    seller_permissions = [  'add_product', 'change_good', 'delete_good', 'view_good',
                            'change_password', 'get_category', 'view_orders', 'update_order_status',
                            'update_product', 'delete_product', 'change_product_availability',
                            "delete_self", "delete_product_parameters", "add_product_parameters", "update_product_parameters",
                            'add_product_image', 'change_product_image', 'delete_product_image',
                            ]
    # права покупателя  
    buyer_permissions = [
                            'view_good', 'buy_good', 'view_order',
                            'add_to_cart', 'view_cart', 'buy_cart',
                            'view_payment', 'buy_payment', 'view_delivery',
                            'buy_delivery', 'view_review', 'buy_review',
                            'change_password', 'get_category',
                            'update_product_in_cart', 'delete_product_from_cart',
                            'order', 'view_orders', 'delete_self', 'add_contact',
                            'change_contact', 'delete_contact', 'view_contact',
                            ]
    
    content_type = ContentType.objects.get_for_model(UserGroup)

    # добавляем права созданным группам
    # для администратора
    for permission in admin_permissions:
        # создаем право, если его не существует
        permission_obj, created = Permission.objects.get_or_create(
            codename=permission,  # кодовое имя права
            name=permission,  # имя права
            content_type=content_type  # тип модели, к которой относится право
        )
        # добавляем право в список прав группы, если его там нет
        if permission_obj not in admin_group.permissions.all():
            admin_group.permissions.add(permission_obj)

    # для продавца
    for permission in seller_permissions:
        # создаем право, если его не существует
        permission_obj, created = Permission.objects.get_or_create(
            codename=permission,  # кодовое имя права
            name=permission,  # имя права
            content_type=content_type  # тип модели, к которой относится право
        )
        # добавляем право в список прав группы, если его там нет
        if permission_obj not in seller_group.permissions.all():
            seller_group.permissions.add(permission_obj)

    # для покупателя
    for permission in buyer_permissions:
        # создаем право, если его не существует
        permission_obj, created = Permission.objects.get_or_create(
            codename=permission,  # кодовое имя права
            name=permission,  # имя права
            content_type=content_type  # тип модели, к которой относится право
        )
        # добавляем право в список прав группы, если его там нет
        if permission_obj not in buyer_group.permissions.all():
            buyer_group.permissions.add(permission_obj)

    admin_group.save()
    seller_group.save()
    buyer_group.save()

    pass   