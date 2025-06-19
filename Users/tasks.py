from celery import shared_task
from .models import MarketUser
from easy_thumbnails.files import get_thumbnailer
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_avatar(user_id):
    """
    Асинхронная задача для генерации миниатюр аватара пользователя.
    """
    try:
        user = MarketUser.objects.get(id=user_id)
        if user.avatar:
            thumbnailer = get_thumbnailer(user.avatar)
            
            # Генерация миниатюр с использованием алиасов, определенных в settings.py
            # Это закеширует их, и при следующем запросе они будут доступны
            thumbnailer.get_thumbnail({'size': (100, 100), 'crop': True}) # small
            thumbnailer.get_thumbnail({'size': (300, 300), 'crop': True}) # medium
            
            logger.info(f"Миниатюры для пользователя {user_id} успешно созданы.")
            return f"Миниатюры для пользователя {user_id} созданы"
        else:
            logger.warning(f"У пользователя {user_id} нет аватара для обработки.")
            return f"Аватар для пользователя {user_id} не найден"
    except MarketUser.DoesNotExist:
        logger.error(f"Пользователь с ID {user_id} не найден.")
        return f"Пользователь с ID {user_id} не найден."
    except Exception as e:
        logger.error(f"Ошибка при обработке аватара для пользователя {user_id}: {e}")
        # Можно добавить логику повторного выполнения задачи
        raise

