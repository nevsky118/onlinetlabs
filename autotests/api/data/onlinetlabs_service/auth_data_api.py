# Генераторы тестовых данных для auth.

from autotests.settings.utils.data_generator_abstraction import DataAbstractionGenerator
from autotests.settings.utils.utils import Randomizer


class AuthRegisterData(DataAbstractionGenerator):
    """
    Генерирует случайный payload для регистрации.

    :ivar email: Тестовый email пользователя.
    :ivar password: Случайный пароль.
    :ivar name: Уникальное имя сущности для теста.
    :ivar data: Словарь с полями email, password, name.
    """

    def __init__(self):
        uid = Randomizer.uuid()
        self.email = self.generate_test_email(id_=uid)
        self.password = f"pass_{Randomizer.random_string(10)}"
        self.name = self.generate_entity_name(id_=uid, name="auth_register")

        self.data = {
            "email": self.email,
            "password": self.password,
            "name": self.name,
        }


class AuthLoginData(DataAbstractionGenerator):
    """
    Генерирует случайный payload для логина.

    :ivar email: Тестовый email пользователя.
    :ivar password: Случайный пароль.
    :ivar data: Словарь с полями email, password.
    """

    def __init__(self):
        uid = Randomizer.uuid()
        self.email = self.generate_test_email(id_=uid)
        self.password = f"pass_{Randomizer.random_string(10)}"

        self.data = {
            "email": self.email,
            "password": self.password,
        }


class AuthExchangeData(DataAbstractionGenerator):
    """
    Генерирует случайный payload для exchange.

    :ivar user_id: Случайный идентификатор пользователя.
    :ivar email: Тестовый email пользователя.
    :ivar data: Словарь с полями user_id, email.
    """

    def __init__(self):
        uid = Randomizer.uuid()
        self.user_id = f"user-{Randomizer.random_string(8)}"
        self.email = self.generate_test_email(id_=uid)

        self.data = {
            "user_id": self.user_id,
            "email": self.email,
        }


def short_password() -> str:
    """Пароль короче 8 символов (вызывает 400)."""
    return "1234567"


def valid_password() -> str:
    """Генерирует валидный пароль (>= 8 символов)."""
    return f"validpass_{Randomizer.random_string(6)}"
