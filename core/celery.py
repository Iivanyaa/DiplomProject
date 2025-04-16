import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Периодические задачи
app.conf.beat_schedule = {
    'check-pending-orders-every-hour': {
        'task': 'apps.orders.tasks.check_pending_orders',
        'schedule': 3600.0,  # Каждый час
    },
}