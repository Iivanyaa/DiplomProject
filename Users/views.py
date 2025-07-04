import os
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter, OpenApiTypes
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import *
from .models import MarketUser, UserGroup, Contact
from django.contrib.auth import authenticate
from social_core.exceptions import AuthException, MissingBackend
from social_django.utils import load_strategy, load_backend
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from .utils import generate_secure_password
from .schema import *
from easy_thumbnails.files import get_thumbnailer
from .tasks import process_avatar # Импортируем нашу новую задачу Celery


# Регистрация покупателя по логину, почте и паролю
@user_register_schema
class UserRegisterView(APIView):
    def post(self, request):
        """
        POST-запрос на регистрацию пользователя.
        Вся логика валидации и создания инкапсулирована в сериализаторе.
        """
        serializer = UserSerializer(data=request.data)

        # is_valid() теперь выполняет все проверки, включая уникальность email/username
        if serializer.is_valid():
            # .save() вызовет наш переопределенный метод .create()
            serializer.save()
            return Response(
                {
                    'message': 'Пользователь успешно зарегистрирован',
                    # serializer.data теперь содержит данные созданного объекта
                    # (без write_only полей, таких как пароль)
                    'data': serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        # Если данные не валидны, возвращаем ошибки от сериализатора
        # Используем статус 400, что является более стандартным для ошибок валидации
        return Response(
            {
                'message': 'Неверные данные',
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
# логин пользователя
@user_login_schema
class LoginView(APIView):
    def post(self, request):
        # создаем объект serializer, передаем ему данные из запроса
        """
        POST-запрос на аутентификацию пользователя.

        Параметры:
        request (Request): объект запроса Django

        Возвращает:
        Response: объект ответа с сообщением об успешной аутентификации,
            если данные валидны и аутентификация прошла успешно,
            или сообщение об ошибке, если данные не валидны
            или аутентификация прошла неудачно.
        """
        serializer = LoginSerializer(data=request.data)
        # если объект serializer валидный, то
        if serializer.is_valid(raise_exception=True):
            # пытаемся аутентифицировать пользователя
            user = authenticate(**serializer.validated_data)
            # если аутентификация прошла успешно
            if user:
                # сохраняем все данные пользователя в сессии
                request.session['user_id'] = user.id
                request.session['username'] = user.username
                # возвращаем ответ, что аутентификация прошла успешно
                return Response({'message': 'Успешная аутентификация'}, status=status.HTTP_200_OK)
        # если аутентификация прошла неудачно
        return Response({'message': 'неверные данные'}, status=status.HTTP_400_BAD_REQUEST)

# выход пользователя из системы
@user_logout_schema
class LogoutView(APIView):
    def post(self, request):
        # удаляем пользователя из сессии
        """
        POST-запрос на выход пользователя из системы.

        Параметры:
        request (Request): объект запроса Django

        Возвращает:
        Response: объект ответа с сообщением об успешном выходе,
            если пользователь аутентифицирован,
            или сообщение об ошибке, если пользователь не аутентифицирован
        """
        request.session.flush()
        # возвращаем ответ, что аутентификация прошла успешно
        return Response({'message': 'Успешный выход'}, status=status.HTTP_200_OK)

# Изменение пароля пользователя
@user_change_password_schema
class ChangePasswordView(APIView):
    def post(self, request):
        # Получаем текущего пользователя из сессии
        """
        POST-запрос на изменение пароля пользователя.

        Параметры:
        request (Request): объект запроса Django

        Возвращает:
        Response: объект ответа с сообщением об успешном изменении пароля,
            если пользователь аутентифицирован и имеет необходимые права,
            или сообщение об ошибке, если пользователь не аутентифицирован,
            не имеет прав, старый пароль неверный, или новый пароль совпадает
            со старым. Также возвращает ошибки, если данные не валидны.
        """

        user_id = request.session.get('user_id')
        if not user_id:
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
        # Получаем объект пользователя по ID
        user = MarketUser.objects.get(id=user_id)
        # Проверяем, имеет ли пользователь право на изменение пароля
        if not user.has_perm('Users.change_password'):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        # Создаем объект serializer, передаем ему данные из запроса
        serializer = ChangePasswordSerializer(data=request.data)
        # Проверяем, валидны ли данные
        if serializer.is_valid(raise_exception=True):
            # Если данные валидны, проверяем старый пароль
            if not check_password(serializer.validated_data['old_password'], user.password):
                return Response({'message': 'Неверный старый пароль'}, status=status.HTTP_400_BAD_REQUEST)
            # Если старый пароль верный, проверяем новый пароль
            if serializer.validated_data['old_password'] == serializer.validated_data['new_password']:
                return Response({'message': 'Новый пароль не может совпадать со старым'}, status=status.HTTP_400_BAD_REQUEST)
            # Обновляем пароль
            user.password = make_password(serializer.validated_data['new_password'])
            user.save()
            # Возвращаем ответ, что пароль успешно изменен
            return Response({'message': 'Пароль успешно изменен'}, status=status.HTTP_200_OK)
        # Если данные не валидны, возвращаем ошибки
        return Response(
            {
                'message': 'Неверные данные',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    

# Удаление пользователя
@delete_user_schema
class DeleteUserView(APIView):
    def delete(self, request):
        # создаем объект serializer, передаем ему данные из запроса
        """
        DELETE-запрос на удаление пользователя.

        Параметры:
        request (Request): объект запроса Django

        Возвращает:
        Response: объект ответа с сообщением об успешном удалении
            пользователя, если пользователь имеет необходимые права, или
            сообщение об ошибке, если таких прав нет.
        """
        serializer = DeleteUserSerializer(data=request.query_params)
        print(serializer.is_valid())
        print(serializer.validated_data)
        print(request.query_params)
        # проверяем, есть ли в запросе id пользователя или username
        if 'id' not in request.query_params and 'username' not in request.query_params or 'id' in request.query_params and request.query_params['id'] == str(request.session.get('user_id')) or 'username' in request.query_params and request.query_params['username'] == request.session.get('username'):
            print('ничего нет в query_params либо id совпадает с id из сессии')
            # если нет, то удаляем текущего пользователя
            # Проверяем, имеет ли пользователь право на самоудаление
            if not MarketUser.AccessCheck(self, request=request, perm='Users.delete_self'):
                return Response({'message': 'Недостаточно прав'}, status=status.HTTP_401_UNAUTHORIZED, content_type='application/json')
            # получаем объеат пользователя из сессии
            user = MarketUser.objects.get(id=request.session.get('user_id'))
            # Удаляем пользователя
            user.delete()
            # Возвращаем ответ, что пользователь успешно удален
            return Response({'message': 'Пользователь успешно удален'}, status=status.HTTP_200_OK, content_type='application/json')
        print('в запросе есть id другого пользователя или username')
        #проверяем не передал ли пользователь свой i
        # если в запросе есть id пользователя или username, то удаляем пользователя по id или username
        # Проверяем, имеет ли пользователь право на удаление пользователя
        if not MarketUser.AccessCheck(self, request=request, perm='Users.delete_user'):
            print('проверку прав на удаление пользователя не прошли')
            print(MarketUser.AccessCheck(self, request=request, perm='Users.delete_user'))
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_401_UNAUTHORIZED, content_type='application/json')
        print('проверку прав на удаление пользователя прошли')
        # удаляем пользователя по id или username
        user = MarketUser.objects.get(id=request.query_params['id'] if 'id' in request.query_params else MarketUser.objects.get(username=request.query_params['username']).id)
        user.delete()
        # Возвращаем ответ, что пользователь успешно удален
        return Response({'message': 'Пользователь успешно удален'}, status=status.HTTP_200_OK, content_type='application/json')


# Изменение данных пользователя
@update_user_data_schema
class UpdateUserView(APIView):
    def put(self, request, perm='Users.update_user'):
        """
        PUT-запрос на изменение данных пользователя.

        Параметры:
        request (Request): объект запроса Django

        Возвращает:
        Response: объект ответа с обновленными данными
            пользователя, если пользователь аутентифицирован и
            имеет необходимые права, или сообщение об ошибке,
            если пользователь не аутентифицирован, не имеет
            прав, или ID пользователя не найден.
        """
        serializer = UserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # проверяем аутентифицирован ли пользователь
        if request.session.get('user_id') is None:
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
        # Получаем ID пользователя из запроса или из сессии
        user_id = serializer.validated_data.get('id') or request.session.get('user_id')
        if not user_id:
            return Response({'message': 'ID пользователя не найден'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Получаем пользователя по ID
        user = MarketUser.objects.filter(id=user_id).first()
        if not user:
            return Response({'message': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)
        
        # Проверяем наличие прав на изменение данных пользователя
        if user_id != request.session.get('user_id') and not MarketUser.AccessCheck(self, request=request, perm=perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        
        # Обновляем данные пользователя
        for field, value in serializer.validated_data.items():
            setattr(user, field, value)
        user.save()
        
        return Response(serializer.data, status=status.HTTP_200_OK)


# удаление данных пользователя
@delete_user_data_schema
class DeleteUserDataView(APIView):
    def delete(self, request, perm='Users.delete_user_data'):
        # проверяем аутентифицирован ли пользователь
        """
        Удаляет выбранные данные пользователя на основе предоставленных данных.

        Параметры:
        request (Request): объект запроса Django
        perm (str): требуемое разрешение для удаления данных пользователя

        Возвращает:
        Response: объект ответа с сообщением об успешном удалении данных, если
            пользователь аутентифицирован, имеет необходимые права и данные
            пользователя существуют. В противном случае возвращает сообщение
            об ошибке, если пользователь не аутентифицирован, не имеет прав,
            или данные пользователя не найдены.
        """
        # Создаем объект serializer, передаем ему данные из запроса
        serializer = DeleteUserDataSerializer(data=request.query_params)
        print(request.query_params)
        print(serializer.is_valid())
        # Проверяем, что данные валидны
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        if request.session.get('user_id') is None:
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
        # Получаем ID пользователя из запроса, если он не указан, то используем ID из сессии
        user_id = request.query_params.get('id') or request.session.get('user_id')
        print(user_id)
        # проверяем наличие пользователя
        try:
            MarketUser.objects.get(id=user_id)
            print(MarketUser.objects.get(id=user_id))
        except MarketUser.DoesNotExist:
            print('пользователь не нашелся')    
            return Response({'message': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)
        # Проверяем наличия прав на удаление данных пользователя
        if user_id != request.session.get('user_id') and not MarketUser.AccessCheck(self, request=request, perm=perm):
            print('проверку прав на удаление данных пользователя не прошли')
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_401_UNAUTHORIZED)
        # Получаем объект пользователя по ID
        user = MarketUser.objects.get(id=user_id)
        print(user)
        # Удаляем выбранные данные
        for field in serializer.validated_data['data_to_delete'].split(','):
            print(field)
            # Проверяем, существует ли поле у пользователя
            if hasattr(user, field):
                print(field)
                # Удаляем поле
                setattr(user, field, None)
                user.save()
            
        # Возвращаем ответ, что данные успешно удалены
            return Response({'message': 'Данные пользователя успешно удалены'}, status=status.HTTP_200_OK)
        # Если данные не валидны, возвращаем ошибки
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# получение данных пользователя по ID
@get_user_data_schema
class GetUserDataView(APIView):
    def get(self, request, perm='Users.get_user_data'):
        # Создаем объект сериализатора, передаем ему данные из запроса
        """
        GET-запрос на получение данных пользователя.

        Параметры:
        request (Request): объект запроса Django
        perm (str): требуемое разрешение для получения данных пользователя

        Возвращает:
        Response: объект ответа с данными пользователя, если пользователь
            аутентифицирован, имеет необходимые права и пользователь
            существует. В противном случае возвращает сообщение об ошибке,
            если пользователь не аутентифицирован, не имеет прав, или
            пользователь не найден.
        """
        # print(request.query_params)
        serializer = GetUserDataSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # print(serializer.validated_data)
        # print(serializer.is_valid())
        # получаем ID пользователя из запроса, если он не указан, то используем ID из сессии
        user_id = serializer.validated_data.get('id') or request.session.get('user_id')
        # print(user_id, request.session.get('user_id'))
        # print(request.session.get('user_id'))
        # print(request.session)
        # проверяем наличия прав на получение данных другого пользователя
        if request.session.get('user_id') is None or user_id != request.session.get('user_id') and not MarketUser.AccessCheck(self, request=request, perm=perm):
            print('проверку прав на получение данных другого пользователя не прошли')
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_401_UNAUTHORIZED , content_type='application/json')
        # проверяем наличие пользователя
        if not MarketUser.objects.filter(id=user_id).exists():
            print('пользователь не нашелся')
            return Response({'message': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

        # Получаем объект пользователя по ID
        user = MarketUser.objects.get(id=user_id)
        
        # Возвращаем данные пользователя
        return Response({
            'message': 'Данные пользователя успешно получены',
            'данные пользователя':UserSerializer(user).data
        }, status=status.HTTP_200_OK)


# восстановление пароля по электроронному адресу
@restore_password_schema
class RestorePasswordView(APIView):
    def post(self, request):
        # Создаем объект сериализатора, передаем ему данные из запроса
        """
        POST-запрос на восстановление пароля пользователя по его электронному адресу.

        Параметры:
        request (Request): объект запроса Django, содержащий электронный адрес пользователя.

        Возвращает:
        Response: объект ответа с сообщением об успешном изменении пароля, если
            пользователь с указанным электронным адресом существует. В противном
            случае возвращает сообщение об ошибке, если пользователь не найден.
        """

        serializer = RestorePasswordSerializer(data=request.data)
        # Проверяем, валидны ли данные
        if serializer.is_valid(raise_exception=True):
            # Получаем объект пользователя по электронному адресу
            try:
                user = MarketUser.objects.get(email=serializer.validated_data['email'])
            except MarketUser.DoesNotExist:
                return Response({'message': 'Пользователь с таким электронным адресом не найден'}, status=status.HTTP_404_NOT_FOUND)
            #Генерируем новый пароль
            new_password = generate_secure_password()
            # Обновляем пароль пользователя
            user.password = make_password(new_password)
            user.save()
            # Отправляем письмо с новым паролем
            send_mail(
                subject='Восстановление пароля',
                from_email=os.getenv('EMAIL_HOST_USER'),
                message=f'Ваш новый пароль: {new_password}',
                recipient_list=[user.email],
                fail_silently=False,
            )
            # Возвращаем ответ, что пароль успешно изменен
            return Response({'message': 'Пароль успешно изменен'}, status=status.HTTP_200_OK)

@contact_schema
class AddContactView(APIView):
    # вьюшка для добавления контакта
    def post(self, request, perm='Users.add_contact'):
        print('вьюшка для добавления контакта')
        serializer = AddContactSerializer(data=request.data)
        print('проверяем валидность сериализатора')
        print(serializer.is_valid())
        if not serializer.is_valid():
            return Response({'message': 'Обязательные поля не заполнены'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        print('проверку сериализатора прошли')
        # проверяем наличие прав на добавление контакта
        print('проверяем наличие прав на добавление контакта')
        if not MarketUser.AccessCheck(self, request=request, perm=perm):
            print('проверку прав на добавление контакта не прошли')
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_401_UNAUTHORIZED , content_type='application/json')
        user = MarketUser.objects.get(id=request.session.get('user_id'))
        # проверяем чтобы контактов было не больше 5
        print('проверяем чтобы контактов было не больше 5')
        if user.contacts.count() >= 5:
            print('проверку чтобы контактов было не больше 5 не прошли')
            return Response({'message': 'Превышено максимальное количество контактов'}, status=status.HTTP_400_BAD_REQUEST)
        # добавляем контакт
        print('добавляем контакт')
        Contact.objects.create(user=user, **serializer.validated_data)
        return Response({'message': 'Контакт успешно добавлен'}, status=status.HTTP_200_OK)
    # вьюшка для изменения контакта по id
    def put(self, request, perm='Users.change_contact'):
        print('проверяем валидность сериализатора')
        serializer = UpdateContactSerializer(data=request.data)
        print(serializer.is_valid())
        print(serializer.validated_data)
        if not serializer.is_valid():
            print('проверку сериализатора не прошли')
            return Response({'message': 'Обязательные поля не заполнены',
                             'errors': serializer.errors}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        print('проверку сериализатора прошли')
        # проверяем наличие прав на изменение контакта
        if not MarketUser.AccessCheck(self, request=request, perm=perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_401_UNAUTHORIZED , content_type='application/json')
        # изменяем контакт
        user = MarketUser.objects.get(id=request.session.get('user_id'))
        try:
            contact = user.contacts.get(id=request.data['id'])
        except Contact.DoesNotExist:
            return Response({'message': 'Контакт не найден'}, status=status.HTTP_404_NOT_FOUND)
        print(contact)
        for field, value in serializer.validated_data.items():
            setattr(contact, field, value)
        contact.save()
        return Response({'message': 'Контакт успешно изменен'}, status=status.HTTP_200_OK)
    # вьюшка для удаления контакта по id
    def delete(self, request, perm='Users.delete_contact'):
        serializer = DeleteContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # проверяем наличие прав на удаление контакта
        if not MarketUser.AccessCheck(self, request=request, perm=perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_401_UNAUTHORIZED , content_type='application/json')
        user = MarketUser.objects.get(id=request.session.get('user_id'))
        # удаляем контакт
        try:
            user.contacts.get(id=request.data['id']).delete()
        except Contact.DoesNotExist:
            return Response({'message': 'Контакт не найден'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'message': 'Контакт успешно удален'}, status=status.HTTP_200_OK)
    # получение контакта по id или всех контактов, если id не передан
    def get(self, request, perm='Users.view_contact'):
        serializer = GetContactSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'message': 'Обязательные поля не заполнены'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        # проверяем наличие прав на просмотр контакта
        if not MarketUser.AccessCheck(self, request=request, perm=perm):
            return Response({'message': 'Недостаточно прав'}, status=status.HTTP_401_UNAUTHORIZED , content_type='application/json')
        user = MarketUser.objects.get(id=request.session.get('user_id'))
        # получаем контакт по id
        if 'id' in request.query_params.keys():
            try:
                contact = user.contacts.get(id=request.query_params['id'])
            except Contact.DoesNotExist:
                return Response({'message': 'Контакт не найден'}, status=status.HTTP_404_NOT_FOUND)
            return Response({'contact': AddContactSerializer(contact).data}, status=status.HTTP_200_OK)
        # получаем все контакты
        contacts = user.contacts.all()
        return Response({'contacts': AddContactSerializer(contacts, many=True).data}, status=status.HTTP_200_OK)
    
# вьюшка для аутентификации через социальные сети
@social_auth_schema
class SocialAuthView(APIView):
    """
    Представление для аутентификации через социальные сети.
    Принимает `backend` (например, 'vk-oauth2', 'google-oauth2')
    и `code` (код авторизации) от клиента.
    """
    def post(self, request):
        serializer = SocialAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        backend_name = serializer.validated_data['backend']
        code = serializer.validated_data['code']

        try:
            # Загружаем стратегию и бэкенд, используя оригинальный объект запроса Django.
            # python-social-auth ожидает django.http.HttpRequest, поэтому мы обращаемся к _request.
            strategy = load_strategy(request._request)
            backend = load_backend(strategy, backend_name)

            # Пытаемся завершить процесс аутентификации.
            # Это обменяет код на токен доступа и создаст/обновит пользователя.
            user = backend.do_auth(code)

            if user:
                # Если аутентификация успешна, устанавливаем пользователя в сессии.
                request.session['user_id'] = user.id
                request.session['username'] = user.username
                return Response(
                    {
                        'message': 'Успешная аутентификация',
                        'user': UserSerializer(user).data # Возвращаем данные пользователя
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'message': 'Аутентификация не удалась'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except MissingBackend:
            return Response(
                {'message': f'Бэкенд "{backend_name}" не найден или не сконфигурирован'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except AuthException as e:
            return Response(
                {'message': f'Ошибка аутентификации через социальную сеть: {e}'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            # Ловим любые другие неожиданные ошибки
            return Response(
                {'message': f'Произошла внутренняя ошибка сервера: {e}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==== НОВЫЙ КЛАСС ДЛЯ РАБОТЫ С АВАТАРАМИ ====
class AvatarUploadView(APIView):
    """
    Представление для загрузки, получения и удаления аватара пользователя.
    """
    @extend_schema(
        tags=["Аватары пользователей"],
        summary="Загрузить или обновить аватар",
        request=AvatarSerializer,
        responses={
            202: OpenApiResponse(description="Аватар принят на обработку."),
            400: OpenApiResponse(description="Неверный формат запроса."),
            401: OpenApiResponse(description="Пользователь не аутентифицирован."),
        }
    )
    def post(self, request):
        """
        POST-запрос для загрузки аватара.
        Принимает multipart/form-data с полем 'avatar'.
        """
        user_id = request.session.get('user_id')
        if not user_id:
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = AvatarSerializer(data=request.data)
        if serializer.is_valid():
            user = MarketUser.objects.get(id=user_id)
            # Сохраняем оригинальный аватар
            user.avatar = serializer.validated_data['avatar']
            user.save()
            
            # Запускаем асинхронную задачу для генерации миниатюр
            process_avatar.delay(user.id)
            
            return Response({'message': 'Аватар принят на обработку'}, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Аватары пользователей"],
        summary="Получить URL аватара и его миниатюр",
        responses={
            200: OpenApiResponse(description="URL аватара и его миниатюр.",
                examples=[OpenApiExample(
                    'Example 1',
                    value={
                        'original': '/media/avatars/user_1.jpg',
                        'thumbnail': '/media/CACHE/images/avatars/user_1.jpg/f0f4a7b7d2.../user_1.jpg'
                    }
                )]
            ),
            401: OpenApiResponse(description="Пользователь не аутентифицирован."),
            404: OpenApiResponse(description="Аватар не найден."),
        }
    )
    def get(self, request):
        """
        GET-запрос для получения URL аватара и его миниатюр.
        """
        user_id = request.session.get('user_id')
        if not user_id:
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            user = MarketUser.objects.get(id=user_id)
            if not user.avatar:
                 return Response({'message': 'Аватар не найден'}, status=status.HTTP_404_NOT_FOUND)

            thumbnailer = get_thumbnailer(user.avatar)
            thumbnails = {
                'original': user.avatar.url,
                'small': thumbnailer.get_thumbnail({'size': (100, 100), 'crop': True}).url,
                'medium': thumbnailer.get_thumbnail({'size': (300, 300), 'crop': True}).url
            }
            return Response(thumbnails, status=status.HTTP_200_OK)

        except MarketUser.DoesNotExist:
            return Response({'message': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Аватары пользователей"],
        summary="Удалить аватар",
        responses={
            200: OpenApiResponse(description="Аватар успешно удален."),
            401: OpenApiResponse(description="Пользователь не аутентифицирован."),
            404: OpenApiResponse(description="Пользователь или аватар не найден."),
        }
    )
    def delete(self, request):
        """
        DELETE-запрос для удаления аватара пользователя.
        """
        user_id = request.session.get('user_id')
        if not user_id:
            return Response({'message': 'Пользователь не аутентифицирован'}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            user = MarketUser.objects.get(id=user_id)
            if not user.avatar:
                return Response({'message': 'У пользователя нет аватара для удаления'}, status=status.HTTP_404_NOT_FOUND)
            
            # Удаляем файл аватара и очищаем поле в модели
            user.avatar.delete(save=True)
            
            return Response({'message': 'Аватар успешно удален'}, status=status.HTTP_200_OK)

        except MarketUser.DoesNotExist:
            return Response({'message': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)