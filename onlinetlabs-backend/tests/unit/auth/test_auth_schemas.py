import pytest
from pydantic import ValidationError

from auth.schemas import LoginRequest, RegisterRequest
from tests.report import autotests

pytestmark = [pytest.mark.unit, pytest.mark.auth]


class TestRegisterRequest:
    @autotests.num("10")
    @autotests.external_id("9f565230-88b7-4d22-bafb-c3827d40ecea")
    @autotests.name("RegisterRequest: валидные данные")
    def test_valid(self):
        """Проверяет создание RegisterRequest с валидными данными."""

        # Act
        with autotests.step("Создаём RegisterRequest с валидным email и паролем"):
            req = RegisterRequest(email="test@example.com", password="securepass123")

        # Assert
        with autotests.step("Проверяем что email сохранён корректно"):
            assert req.email == "test@example.com"

    @autotests.num("11")
    @autotests.external_id("3ff24f51-227e-4a56-a954-e31ceb74edd8")
    @autotests.name("RegisterRequest: невалидный email отклоняется")
    def test_invalid_email(self):
        """Проверяет что невалидный email вызывает ValidationError."""

        # Act & Assert
        with autotests.step("Создаём RegisterRequest с невалидным email"):
            with pytest.raises(ValidationError):
                RegisterRequest(email="not-an-email", password="securepass123")

    @autotests.num("12")
    @autotests.external_id("9c3a3a1b-2276-470e-b1e3-4a3ec3d9a862")
    @autotests.name("RegisterRequest: короткий пароль отклоняется")
    def test_short_password(self):
        """Проверяет что короткий пароль вызывает ValidationError."""

        # Act & Assert
        with autotests.step("Создаём RegisterRequest с коротким паролем"):
            with pytest.raises(ValidationError):
                RegisterRequest(email="test@example.com", password="short")


class TestLoginRequest:
    @autotests.num("13")
    @autotests.external_id("bf961588-41f2-4d25-acab-959d5a06ffbc")
    @autotests.name("LoginRequest: валидные данные")
    def test_valid(self):
        """Проверяет создание LoginRequest с валидными данными."""

        # Act
        with autotests.step("Создаём LoginRequest"):
            req = LoginRequest(email="test@example.com", password="pass")

        # Assert
        with autotests.step("Проверяем что email сохранён"):
            assert req.email == "test@example.com"
