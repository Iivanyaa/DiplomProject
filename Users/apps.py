from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'Users'

    # метод который будет выполнен при запуске приложения
    def ready(self):
        # создаем 3 группы: администратор, продавец, покупатель
        from .models import UserGroup
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        # если группа 'Admin' не существует, то создаем ее,
        # иначе, просто получаем ее
        admin_group, created = UserGroup.objects.get_or_create(name='Admin')  # администратор
        seller_group, created = UserGroup.objects.get_or_create(name='Seller')  # продавец
        buyer_group, created = UserGroup.objects.get_or_create(name='Buyer')  # покупатель

        # создаем права
        # права администратора
        admin_permissions = ['add_user', 'change_user', 'delete_user', 'view_user'],
        # права продавца
        seller_permissions = ['add_good', 'change_good', 'delete_good', 'view_good'],
        # права покупателя  
        buyer_permissions = [
            'view_good', 'buy_good', 'view_order',
            'buy_order', 'view_cart', 'buy_cart',
            'view_payment', 'buy_payment', 'view_delivery',
            'buy_delivery', 'view_review', 'buy_review'
            ]
        
        content_type = ContentType.objects.get_for_model(UserGroup)

        # добавляем права созданным группам
        for permission in admin_permissions:
            permission_obj, created = Permission.objects.get_or_create(codename=permission, name=permission, content_type=content_type)
            admin_group.permissions.add(permission_obj)
        
        for permission in seller_permissions:
            permission_obj, created = Permission.objects.get_or_create(codename=permission, name=permission, content_type=content_type)
            seller_group.permissions.add(permission_obj)
        
        for permission in buyer_permissions:
            permission_obj, created = Permission.objects.get_or_create(codename=permission, name=permission, content_type=content_type)
            buyer_group.permissions.add(permission_obj)


