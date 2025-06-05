from django.db import models
from django.contrib.auth.models import Group, User
from rest_framework.response import Response
from rest_framework import status


class MarketUser(User):
    # поле для номера телефона
    phone_number = models.CharField(max_length=20, blank=True, null=True)
        # это поле будет хранить номер телефона пользователя
    # тип пользователя (Buyer, Seller, Admin)
    USER_TYPES = (
        ('Seller', 'Продавец'),  # тип Seller - продавец
        ('Buyer', 'Покупатель'),  # тип Buyer - покупатель
        ('Admin', 'Администратор'),  # тип Admin - администратор
    )
    user_type = models.CharField(
        max_length=20,  # длинна строки 20 символов
        blank=True,  # поле может быть пустым
        null=True,  # поле может быть Null
        choices=USER_TYPES,  # типы пользователей
        default='Buyer'  # по умолчанию - покупатель
    )
    
    def AccessCheck(self, request, perm: str):
        user_id = request.session.get('user_id')
        if not user_id:
            return False
        # Получаем объект пользователя по ID
        user = MarketUser.objects.get(id=user_id)
        # Проверяем, имеет ли пользователь право на действие
        if not user.has_perm(perm):
            return False
        return True

# создаем моедль группы покупателей
class UserGroup(Group):
    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'


# создаем модель контактов юзера
class Contact(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь',
                             related_name='contacts', blank=True,
                             on_delete=models.CASCADE)

    city = models.CharField(max_length=50, verbose_name='Город')
    street = models.CharField(max_length=100, verbose_name='Улица')
    house = models.CharField(max_length=15, verbose_name='Дом', blank=True)
    structure = models.CharField(max_length=15, verbose_name='Корпус', blank=True)
    building = models.CharField(max_length=15, verbose_name='Строение', blank=True)
    apartment = models.CharField(max_length=15, verbose_name='Квартира', blank=True)
    phone = models.CharField(max_length=20, verbose_name='Телефон')

    class Meta:
        verbose_name = 'Контакты пользователя'
        verbose_name_plural = "Список контактов пользователя"

    def __str__(self):
        return f'{self.city} {self.street} {self.house}'
