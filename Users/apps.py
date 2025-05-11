from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'Users'

    #метод который будет выполнен при запуске приложения
    def ready(self):
        from . import signals  # noqa