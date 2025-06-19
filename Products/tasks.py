from celery import shared_task
from easy_thumbnails.files import get_thumbnailer

@shared_task
def process_product_image(product_image_id):
    """
    Асинхронная задача для генерации миниатюр изображения продукта.
    """
    # Импортируем модель здесь, чтобы избежать циклических зависимостей,
    # если tasks.py импортирует что-либо из models, а models импортирует tasks.
    from .models import ProductImage

    try:
        product_image = ProductImage.objects.get(id=product_image_id)
        if product_image.image:
            # Обращение к .thumbnail генерирует миниатюры, если они еще не существуют.
            # Для определенных размеров:
            thumbnailer = get_thumbnailer(product_image.image)
            # Доступ к URL-ам миниатюр для их генерации (если настроено создание на лету)
            thumbnailer['small'].url # Например, размер 100x100, определенный в настройках easy-thumbnails
            thumbnailer['medium'].url # Например, размер 300x300, определенный в настройках easy-thumbnails
            print(f"Миниатюры для изображения продукта ID {product_image_id} сгенерированы.")
    except ProductImage.DoesNotExist:
        print(f"Изображение продукта с ID {product_image_id} не найдено.")
    except Exception as e:
        print(f"Ошибка при обработке изображения продукта ID {product_image_id}: {e}")