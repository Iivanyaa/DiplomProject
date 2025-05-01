from Market.settings import GROUPS, PERMISSIONS
from Users.models import MarketUser

def create_groups_and_permissions():
    from django.contrib.auth.models import Group, Permission
    for group in GROUPS:
        group_obj, created = Group.objects.get_or_create(name=group['name'])
        for permission in group['permissions']:
            permission_obj, created = Permission.objects.get_or_create(codename=permission, name=permission)
            group_obj.permissions.add(permission_obj)

    for permission in PERMISSIONS:
        content_type = content_type.objects.get_for_model(MarketUser)  # Замените MarketUser на модель, которую вы хотите связать с разрешением
        permission_obj, created = Permission.objects.get_or_create(
            codename=permission['codename'],
            name=permission['name'],
            content_type=content_type
        )