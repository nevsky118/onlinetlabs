from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from app.auth.dependencies import create_backend_token, decode_backend_token, get_current_user
from app.config import settings
from tests.report import autotests

pytestmark = [pytest.mark.unit, pytest.mark.auth]

SECRET = "test-secret"


class TestDecodeBackendToken:
    @autotests.num("20")
    @autotests.external_id("7441385f-ba85-4692-ad2b-98225cd97757")
    @autotests.name("decode_backend_token: валидный токен")
    def test_valid_token(self):
        """Проверяет декодирование валидного JWT-токена."""

        # Arrange
        payload = {
            "sub": "user-123",
            "role": "student",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
        token = jwt.encode(payload, SECRET, algorithm="HS256")

        # Act
        with autotests.step("Декодируем валидный JWT-токен"):
            decoded = decode_backend_token(token, SECRET)

        # Assert
        with autotests.step("Проверяем payload содержит sub и role"):
            assert decoded["sub"] == "user-123"
            assert decoded["role"] == "student"

    @autotests.num("21")
    @autotests.external_id("a9bcca8d-7c80-47a3-bfeb-595aab739fd9")
    @autotests.name("decode_backend_token: просроченный токен вызывает исключение")
    def test_expired_token(self):
        """Проверяет что просроченный токен вызывает исключение."""

        # Arrange
        payload = {
            "sub": "user-123",
            "role": "student",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        }
        token = jwt.encode(payload, SECRET, algorithm="HS256")

        # Act & Assert
        with autotests.step("Декодируем просроченный токен"):
            with pytest.raises(Exception):
                decode_backend_token(token, SECRET)

    @autotests.num("22")
    @autotests.external_id("f4329541-1937-4b90-8efe-9f715bbc6162")
    @autotests.name("decode_backend_token: невалидный токен вызывает исключение")
    def test_invalid_token(self):
        """Проверяет что мусорный токен вызывает исключение."""

        # Act & Assert
        with autotests.step("Декодируем невалидный токен"):
            with pytest.raises(Exception):
                decode_backend_token("garbage-token", SECRET)


class TestGetCurrentUser:
    @autotests.num("23")
    @autotests.external_id("ea04fb38-4ee6-4eb7-9226-77448b492ba4")
    @autotests.name("get_current_user: валидный токен возвращает пользователя")
    async def test_valid_token_returns_user(self):
        # Arrange
        token = create_backend_token("user-123", "student")
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Act
        with autotests.step("Вызываем get_current_user с валидным токеном"):
            result = await get_current_user(creds)

        # Assert
        with autotests.step("Проверяем id и role"):
            assert result["id"] == "user-123"
            assert result["role"] == "student"

    @autotests.num("24")
    @autotests.external_id("9f08e762-80ab-4bfe-ac0e-b36a7cc2cb96")
    @autotests.name("get_current_user: просроченный токен вызывает 401")
    async def test_expired_token_raises_401(self):
        # Arrange
        payload = {
            "sub": "user-123",
            "role": "student",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        }
        token = jwt.encode(payload, settings.api.jwt_secret, algorithm="HS256")
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Act & Assert
        with autotests.step("Вызываем get_current_user с просроченным токеном"):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(creds)
            assert exc_info.value.status_code == 401

    @autotests.num("25")
    @autotests.external_id("8116ce8b-9e0c-43d6-9389-3a31e115aaaf")
    @autotests.name("get_current_user: мусорный токен вызывает 401")
    async def test_garbage_token_raises_401(self):
        # Arrange
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="garbage")

        # Act & Assert
        with autotests.step("Вызываем get_current_user с мусорным токеном"):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(creds)
            assert exc_info.value.status_code == 401

    @autotests.num("26")
    @autotests.external_id("9e47ab17-f4a5-4500-aa9c-15a85b748f13")
    @autotests.name("get_current_user: токен без sub вызывает 401")
    async def test_no_sub_raises_401(self):
        # Arrange
        payload = {
            "role": "student",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
        token = jwt.encode(payload, settings.api.jwt_secret, algorithm="HS256")
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Act & Assert
        with autotests.step("Вызываем get_current_user с токеном без sub"):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(creds)
            assert exc_info.value.status_code == 401
