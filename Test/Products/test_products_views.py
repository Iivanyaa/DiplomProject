# tests/products/test_views.py
import pytest
from django.urls import reverse
from rest_framework import status
from Products.models import Product, Category, CartProduct, Cart, Parameters
from Users.models import MarketUser, Contact

@pytest.mark.django_db
class TestProductsView:
    @pytest.fixture(autouse=True)
    def setup(self, product, category):
        self.url = reverse('Products')
        self.product = product
        self.category = category

    def test_get_all_products(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['products']) == 1

    def test_create_product_as_seller(self, authenticated_seller_client):
        data = {
            "name": "New Product",
            "price": 199.99,
            "description": "New Description",
            "quantity": 10
        }
        response = authenticated_seller_client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Product.objects.count() == 2

    def test_create_product_unauthorized(self, api_client):
        response = api_client.post(self.url, {
            "name": "New Product",
            "price": 199.99,
            "description": "New Description",
            "quantity": 10
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['message'] == 'Недостаточно прав'

    def test_update_product(self, authenticated_seller_client):
        data = {
            "id": self.product.id,
            "price": '150.00',
            "description": "Updated Description"
        }
        response = authenticated_seller_client.put(self.url, data)
        self.product.refresh_from_db()
        assert self.product.price == 150.00
        assert response.status_code == status.HTTP_200_OK
        assert self.product.description == "Updated Description"
        assert self.product.is_available is True

    def test_delete_product(self, authenticated_seller_client):
        # Проверяем существование продукта
        assert Product.objects.filter(id=self.product.id).exists()
    
        # Отправляем DELETE-запрос с параметром в URL
        response = authenticated_seller_client.delete(
            f"{self.url}?id={self.product.id}",
            format='json'
        )
    
        # Проверяем статус и отсутствие продукта
        assert response.status_code == status.HTTP_200_OK
        assert not Product.objects.filter(id=self.product.id).exists()

    # тестируем изменение продавцом доступности товаров
    def test_update_product_availability(self, authenticated_seller_client):
        self.seller_product_2 = Product.objects.create(
            name="Product 2",
            price=199.99,
            description="Product 2 Description",
            quantity=10,
            seller=self.product.seller
        )
        assert self.seller_product_2.is_available is True and self.product.is_available is True and Product.objects.count() == 2
        data = {
            "id": self.product.id,
            "is_available": False
        }
        response = authenticated_seller_client.put(reverse('ChangeProducts'), data)
        self.product.refresh_from_db()
        self.seller_product_2.refresh_from_db()
        assert self.product.is_available is False
        assert self.seller_product_2.is_available is True

    # тестируем изменение доступности всех товаров продавца без указания id
    def test_update_all_products_availability(self, authenticated_seller_client):
        self.seller_product_2 = Product.objects.create(
            name="Product 2",
            price=199.99,
            description="Product 2 Description",
            quantity=10,
            seller=self.product.seller
        )
        assert self.seller_product_2.is_available is True and self.product.is_available is True and Product.objects.count() == 2
        data = {
            "is_available": False
        }
        response = authenticated_seller_client.put(reverse('ChangeProducts'), data)
        self.product.refresh_from_db()
        self.seller_product_2.refresh_from_db()
        assert self.product.is_available is False
        assert self.seller_product_2.is_available is False

    # тестируем изменение доступности товара покупателем
    def test_update_product_availability_by_buyer(self, authenticated_buyer_client):
        data = {
            "id": self.product.id,
            "is_available": False
        }
        response = authenticated_buyer_client.put(reverse('ChangeProducts'), data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['message'] == 'Недостаточно прав'

#тестируем работу с параметрами продукта
@pytest.mark.django_db
class TestProductParametersView:
    @pytest.fixture(autouse=True)
    def setup(self, product):
        self.url = reverse('ChangeProducts')
        self.product = product

    # --- Тесты для добавления параметров (POST) ---

    def test_add_parameter_success(self, authenticated_seller_client):
        """Проверка успешного добавления параметра продавцом."""
        data = {
            "product_id": self.product.id,
            "name": "Цвет",
            "value": "Красный"
        }
        response = authenticated_seller_client.post(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Параметры продукта успешно добавлены'
        assert self.product.parameters.count() == 1
        param = self.product.parameters.first()
        assert param.name == "Цвет"
        assert param.value == "Красный"

    def test_add_parameter_without_value(self, authenticated_seller_client):
        """Проверка добавления параметра без значения (value is optional)."""
        data = {
            "product_id": self.product.id,
            "name": "Материал"
        }
        response = authenticated_seller_client.post(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        assert self.product.parameters.count() == 1
        param = self.product.parameters.first()
        assert param.name == "Материал"
        assert param.value is None # Проверяем, что значение None

    def test_add_parameter_to_another_seller_product(self, product_another_seller, authenticated_seller_client):
        """Попытка добавления параметра к продукту другого продавца."""
        data = {
            "product_id": product_another_seller.id, # Продукт другого продавца
            "name": "Размер",
            "value": "XL"
        }
        response = authenticated_seller_client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['message'] == 'Продукт относится к другому продавцу'
        assert product_another_seller.parameters.count() == 0

    def test_add_parameter_unauthorized_buyer(self, api_client, buyer_user):
        """Попытка добавления параметра покупателем (недостаточно прав)."""
        data = {
            "product_id": self.product.id,
            "name": "Вес",
            "value": "1 кг"
        }
        response = api_client.post(self.url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['message'] == 'Недостаточно прав'
        assert self.product.parameters.count() == 0

    def test_add_parameter_unauthenticated(self, api_client, buyer_user):
        """Попытка добавления параметра неавторизованным пользователем."""
        data = {
            "product_id": self.product.id,
            "name": "Тип",
            "value": "Электронный"
        }
        response = api_client.post(self.url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN # Или 403, в зависимости от вашей настройки DRF
        assert self.product.parameters.count() == 0

    def test_add_parameter_missing_product_id(self, authenticated_seller_client):
        """Попытка добавления параметра без product_id."""
        data = {
            "name": "Форма",
            "value": "Круг"
        }
        response = authenticated_seller_client.post(self.url, data)
        # Сериализатор ProductParametersSerializer не существует в вашем коде.
        # Предполагается, что вы используете CreateParametersSerializer.
        # CreateParametersSerializer требует product_id, поэтому он должен выдать ошибку валидации.
        assert response.status_code == status.HTTP_400_BAD_REQUEST 
        assert 'product_id' in response.data # Проверяем, что есть ошибка по product_id
        assert self.product.parameters.count() == 0

    def test_add_parameter_missing_name(self, authenticated_seller_client):
        """Попытка добавления параметра без name."""
        data = {
            "product_id": self.product.id,
            "value": "Синий"
        }
        response = authenticated_seller_client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data # Проверяем, что есть ошибка по name
        assert self.product.parameters.count() == 0

    # --- Тесты для изменения параметров (PATCH) ---

    def test_update_parameter_success(self, authenticated_seller_client):
        """Проверка успешного изменения параметра продавцом."""
        param = Parameters.objects.create(
            product=self.product,
            name="Цвет",
            value="Красный"
        )
        data = {
            "product_id": self.product.id,
            "parameters_id": param.id,
            "name": "Цвет", # name обязателен для UpdateParametersSerializer
            "value": "Синий"
        }
        response = authenticated_seller_client.patch(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Параметры продукта успешно изменены'
        param.refresh_from_db()
        assert param.name == "Цвет"
        assert param.value == "Синий"

    def test_update_parameter_change_name_and_value(self, authenticated_seller_client):
        """Проверка изменения имени и значения параметра."""
        param = Parameters.objects.create(
            product=self.product,
            name="Размер",
            value="M"
        )
        data = {
            "product_id": self.product.id,
            "parameters_id": param.id,
            "name": "Габариты",
            "value": "Большой"
        }
        response = authenticated_seller_client.patch(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        param.refresh_from_db()
        assert param.name == "Габариты"
        assert param.value == "Большой"

    def test_update_parameter_only_value(self, authenticated_seller_client):
        """Проверка изменения только значения параметра (name остается прежним)."""
        param = Parameters.objects.create(
            product=self.product,
            name="Материал",
            value="Хлопок"
        )
        data = {
            "product_id": self.product.id,
            "parameters_id": param.id,
            "name": "Материал", # name все еще обязателен
            "value": "Шелк"
        }
        response = authenticated_seller_client.patch(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        param.refresh_from_db()
        assert param.name == "Материал"
        assert param.value == "Шелк"

    def test_update_parameter_to_another_seller_product(self, product_another_seller, authenticated_seller_client):
        """Попытка изменения параметра продукта другого продавца."""
        param = Parameters.objects.create(
            product=product_another_seller,
            name="Вес",
            value="500г"
        )
        data = {
            "product_id": product_another_seller.id,
            "parameters_id": param.id,
            "name": "Вес",
            "value": "1кг"
        }
        response = authenticated_seller_client.patch(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['message'] == 'Продукт относится к другому продавцу'
        param.refresh_from_db()
        assert param.value == "500г" # Значение не должно измениться

    def test_update_parameter_unauthorized_buyer(self, api_client):
        """Попытка изменения параметра покупателем."""
        param = Parameters.objects.create(
            product=self.product,
            name="Форма",
            value="Квадрат"
        )
        data = {
            "product_id": self.product.id,
            "parameters_id": param.id,
            "name": "Форма",
            "value": "Круг"
        }
        response = api_client.patch(self.url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['message'] == 'Недостаточно прав'
        param.refresh_from_db()
        assert param.value == "Квадрат"

    def test_update_parameter_missing_product_id(self, authenticated_seller_client):
        """Попытка изменения параметра без product_id."""
        param = Parameters.objects.create(
            product=self.product,
            name="Тип",
            value="Обычный"
        )
        data = {
            "parameters_id": param.id,
            "name": "Тип",
            "value": "Улучшенный"
        }
        response = authenticated_seller_client.patch(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'product_id' in response.data # Проверяем, что есть ошибка валидации по product_id
        param.refresh_from_db()
        assert param.value == "Обычный"

    def test_update_parameter_missing_parameters_id(self, authenticated_seller_client):
        """Попытка изменения параметра без parameters_id."""
        # Создаем параметр, но не используем его ID в запросе
        Parameters.objects.create(
            product=self.product,
            name="Размер",
            value="S"
        )
        data = {
            "product_id": self.product.id,
            "name": "Размер",
            "value": "L"
        }
        response = authenticated_seller_client.patch(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'parameters_id' in response.data # Должна быть ошибка валидации по parameters_id

    def test_update_parameter_non_existent_parameter_id(self, authenticated_seller_client):
        """Попытка изменения несуществующего параметра."""
        data = {
            "product_id": self.product.id,
            "parameters_id": 9999, # Несуществующий ID
            "name": "Тест",
            "value": "Значение"
        }
        response = authenticated_seller_client.patch(self.url, data)
        assert response.status_code == status.HTTP_404_NOT_FOUND # Ожидаем 404, если get не найдет
        # Или 500, если не обрабатывается исключение DoesNotExist
        # В вашем коде Product.objects.get(...).parameters.get(...) может вызвать исключение.
        # Лучше добавить try-except в самой вьюшке.

    # --- Тесты для удаления параметров (DELETE) ---

    def test_delete_specific_parameter_success(self, authenticated_seller_client):
        """Проверка успешного удаления конкретного параметра продавцом."""
        param1 = Parameters.objects.create(product=self.product, name="Цвет", value="Красный")
        param2 = Parameters.objects.create(product=self.product, name="Материал", value="Дерево")
        assert self.product.parameters.count() == 2

        data = {
            "product_id": self.product.id,
            "parameters_id": param1.id
        }
        response = authenticated_seller_client.delete(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Параметры продукта успешно удалены'
        assert self.product.parameters.count() == 1
        assert not self.product.parameters.filter(id=param1.id).exists()
        assert self.product.parameters.filter(id=param2.id).exists()

    def test_delete_all_parameters_success(self, authenticated_seller_client):
        """Проверка успешного удаления всех параметров для продукта."""
        Parameters.objects.create(product=self.product, name="Цвет", value="Красный")
        Parameters.objects.create(product=self.product, name="Материал", value="Дерево")
        assert self.product.parameters.count() == 2

        data = {
            "product_id": self.product.id # parameters_id не указан
        }
        response = authenticated_seller_client.delete(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Параметры продукта успешно удалены'
        assert self.product.parameters.count() == 0

    def test_delete_parameter_from_another_seller_product(self, product_another_seller, authenticated_seller_client):
        """Попытка удаления параметра продукта другого продавца."""
        param = Parameters.objects.create(
            product=product_another_seller,
            name="Размер",
            value="S"
        )
        assert product_another_seller.parameters.count() == 1

        data = {
            "product_id": product_another_seller.id,
            "parameters_id": param.id
        }
        response = authenticated_seller_client.delete(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['message'] == 'Продукт относится к другому продавцу'
        assert product_another_seller.parameters.count() == 1 # Параметр не должен быть удален

    def test_delete_parameter_unauthorized_buyer(self, authenticated_buyer_client):
        """Попытка удаления параметра покупателем."""
        param = Parameters.objects.create(product=self.product, name="Вес", value="100г")
        assert self.product.parameters.count() == 1

        data = {
            "product_id": self.product.id,
            "parameters_id": param.id
        }
        response = authenticated_buyer_client.delete(self.url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['message'] == 'Недостаточно прав'
        assert self.product.parameters.count() == 1

    def test_delete_parameter_missing_product_id(self, authenticated_seller_client):
        """Попытка удаления параметра без product_id."""
        param = Parameters.objects.create(product=self.product, name="Тест", value="Значение")
        assert self.product.parameters.count() == 1

        data = {
            "parameters_id": param.id
        }
        response = authenticated_seller_client.delete(self.url, data)
        # Ваш DeleteParametersSerializer требует product_id
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'product_id' in response.data # Проверяем, что есть ошибка по product_id
        assert self.product.parameters.count() == 1

    def test_delete_non_existent_parameter(self, authenticated_seller_client):
        """Попытка удаления несуществующего параметра."""
        assert self.product.parameters.count() == 0 # Убедимся, что нет параметров

        data = {
            "product_id": self.product.id,
            "parameters_id": 9999 # Несуществующий ID
        }
        response = authenticated_seller_client.delete(self.url, data)
        assert response.status_code == status.HTTP_404_NOT_FOUND # Ожидаем 404, если get не найдет
        assert response.data['message'] == 'Такого параметра не существует'
        
   

@pytest.mark.django_db
class TestCategoriesView:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.url = reverse('Categories')

    def test_create_category_as_admin(self, authenticated_admin_client):
        data = {"name": "New Category"}
        response = authenticated_admin_client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Category.objects.count() == 1

    def test_delete_category(self, category, authenticated_admin_client):
        data = {"id": category.id}
        response = authenticated_admin_client.delete(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        assert Category.objects.count() == 0

@pytest.mark.django_db
class TestCartView:
    @pytest.fixture(autouse=True)
    def setup(self, buyer_user, product):
        self.url = reverse('Cart')
        self.buyer = buyer_user
        self.product = product

    def test_add_to_cart(self, authenticated_buyer_client):
        data = {"id": self.product.id, "quantity": 2}
        response = authenticated_buyer_client.patch(reverse('Products'), data)
        assert response.status_code == status.HTTP_200_OK
        assert CartProduct.objects.count() == 1

    def test_get_cart(self, authenticated_buyer_client):
        response = authenticated_buyer_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert 'Cart_products' in response.data

    def test_checkout_cart(self, authenticated_buyer_client):
        # Добавляем товар в корзину
        cart, _ = Cart.objects.get_or_create(user=self.buyer)
        CartProduct.objects.create(
            cart=Cart.objects.get(user=self.buyer),
            product=self.product,
            quantity=10
        )
        contact = Contact.objects.create(user=self.buyer, city='City', street='Street', phone='1234567890')
        response = authenticated_buyer_client.post(self.url)
        assert response.status_code == status.HTTP_201_CREATED
        self.product.refresh_from_db()
        assert self.product.quantity == 0  # Исходное количество было 10
        assert self.product.is_available is False

    def test_remove_from_cart(self, authenticated_buyer_client):
        # Создаем корзину и добавляем товар
        cart, _ = Cart.objects.get_or_create(user=self.buyer)
        CartProduct.objects.create(cart=cart, product=self.product, quantity=1)

        # Проверяем, что товар в корзине
        assert cart.products.count() == 1

        # Отправляем DELETE-запрос
        data = {"id": self.product.id}
        response = authenticated_buyer_client.delete(
            reverse('Cart'),
            data,
            format='json'
        )

        # Проверяем ответ и состояние корзины
        assert response.status_code == status.HTTP_200_OK
        assert cart.products.count() == 0