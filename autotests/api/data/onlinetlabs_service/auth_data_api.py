# Test data generators for auth.

from autotests.settings.utils.data_generator_abstraction import DataAbstractionGenerator
from autotests.settings.utils.utils import Randomizer


class AuthRegisterData(DataAbstractionGenerator):
    """
    Generates a random payload for registration.

    :ivar email: Test user email.
    :ivar password: Random password.
    :ivar name: Unique entity name for the test.
    :ivar data: Dictionary with the email, password, name fields.
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
    Generates a random payload for login.

    :ivar email: Test user email.
    :ivar password: Random password.
    :ivar data: Dictionary with the email, password fields.
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
    Generates a random payload for exchange.

    :ivar user_id: Random user identifier.
    :ivar email: Test user email.
    :ivar data: Dictionary with the user_id, email fields.
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
    """Password shorter than 8 characters (triggers a 400)."""
    return "1234567"


def valid_password() -> str:
    """Generates a valid password (>= 8 characters)."""
    return f"validpass_{Randomizer.random_string(6)}"
