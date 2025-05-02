import secrets
import string

def generate_secure_password(length=12):
    # Создаем алфавит: буквы (верхний/нижний регистр), цифры, спецсимволы
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    
    # Генерируем пароль, выбирая случайные символы из алфавита
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    return password