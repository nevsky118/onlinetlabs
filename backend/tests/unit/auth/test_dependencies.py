from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from jose import JWTError, jwt
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import (
    assert_equal,
    assert_in,
    assert_is_none,
    assert_true,
)

from auth.dependencies import (
    create_backend_token,
    decode_backend_token,
    require_admin,
    verify_jwt_for_ws,
)
from config import settings

pytestmark = [pytest.mark.unit, pytest.mark.auth]


class TestBackendTokenRoundTrip:
    @autotest.num("700")
    @autotest.external_id("a1b2c3d4-e5f6-4708-8901-234567890abc")
    @autotest.name("create_backend_token + decode_backend_token: успешный round-trip")
    def test_a1b2c3d4_encode_decode_returns_sub_and_role(self):
        with autotest.step("Arrange: формируем user_id и role"):
            user_id = "user-700"
            role = "student"

        with autotest.step("Act: encode → decode тем же секретом"):
            token = create_backend_token(user_id, role)
            payload = decode_backend_token(token, settings.api.jwt_secret)

        with autotest.step("Assert: sub и role совпадают"):
            assert_equal(payload["sub"], user_id, "sub claim")
            assert_equal(payload["role"], role, "role claim")
            assert_in("exp", payload, "exp claim присутствует")

    @autotest.num("701")
    @autotest.external_id("b2c3d4e5-f607-4809-8a01-34567890abcd")
    @autotest.name("decode_backend_token: неверный секрет → JWTError")
    def test_b2c3d4e5_wrong_secret_raises_jwterror(self):
        with autotest.step("Arrange: выпускаем токен реальным секретом"):
            token = create_backend_token("user-701", "student")

        with autotest.step("Act + Assert: decode чужим секретом падает с JWTError"):
            with pytest.raises(JWTError):
                decode_backend_token(token, "wrong-secret")

    @autotest.num("702")
    @autotest.external_id("c3d4e5f6-0708-490a-8b12-4567890abcde")
    @autotest.name("decode_backend_token: истёкший токен → JWTError")
    def test_c3d4e5f6_expired_token_raises_jwterror(self):
        with autotest.step("Arrange: вручную выпускаем токен с exp в прошлом"):
            past = datetime.now(UTC) - timedelta(minutes=10)
            payload = {"sub": "user-702", "role": "student", "exp": past}
            expired_token = jwt.encode(payload, settings.api.jwt_secret, algorithm="HS256")

        with autotest.step("Act + Assert: decode падает с JWTError"):
            with pytest.raises(JWTError):
                decode_backend_token(expired_token, settings.api.jwt_secret)


class TestVerifyJwtForWs:
    @autotest.num("703")
    @autotest.external_id("d4e5f607-0809-4a0b-8c23-567890abcdef")
    @autotest.name("verify_jwt_for_ws: None → None")
    async def test_d4e5f607_none_returns_none(self):
        with autotest.step("Act: вызываем без токена"):
            result = await verify_jwt_for_ws(None)

        with autotest.step("Assert: возвращает None"):
            assert_is_none(result, "result is None")

    @autotest.num("704")
    @autotest.external_id("e5f60708-090a-4b0c-8d34-67890abcdef0")
    @autotest.name("verify_jwt_for_ws: валидный токен → dict с id и role")
    async def test_e5f60708_valid_token_returns_user_dict(self):
        with autotest.step("Arrange: выпускаем валидный токен"):
            token = create_backend_token("user-704", "admin")

        with autotest.step("Act: верифицируем"):
            result = await verify_jwt_for_ws(token)

        with autotest.step("Assert: dict содержит id и role"):
            assert_true(result is not None, "result не None")
            assert_equal(result["id"], "user-704", "id claim")
            assert_equal(result["role"], "admin", "role claim")

    @autotest.num("705")
    @autotest.external_id("f6070809-0a0b-4c0d-8e45-7890abcdef01")
    @autotest.name("verify_jwt_for_ws: мусорная строка → None")
    async def test_f6070809_garbage_returns_none(self):
        with autotest.step("Act: пытаемся верифицировать мусор"):
            result = await verify_jwt_for_ws("not-a-real-jwt")

        with autotest.step("Assert: None, исключение проглочено"):
            assert_is_none(result, "result is None")


class TestRequireAdmin:
    @autotest.num("706")
    @autotest.external_id("0708090a-0b0c-4d0e-8f56-890abcdef012")
    @autotest.name("require_admin: admin проходит, возвращает того же user")
    def test_0708090a_admin_passes_through(self):
        with autotest.step("Arrange: dict с role=admin"):
            user = {"id": "user-706", "role": "admin"}

        with autotest.step("Act: вызываем зависимость напрямую"):
            result = require_admin(current_user=user)

        with autotest.step("Assert: получаем тот же объект"):
            assert_equal(result, user, "returns the same user dict")

    @autotest.num("707")
    @autotest.external_id("08090a0b-0c0d-4e0f-8067-90abcdef0123")
    @autotest.name("require_admin: student → HTTPException 403")
    def test_08090a0b_non_admin_raises_403(self):
        with autotest.step("Arrange: dict с role=student"):
            user = {"id": "user-707", "role": "student"}

        with autotest.step("Act + Assert: ожидаем 403"):
            with pytest.raises(HTTPException) as exc_info:
                require_admin(current_user=user)
            assert_equal(exc_info.value.status_code, 403, "status_code = 403")
