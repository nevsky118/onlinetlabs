"""Тесты verify_password_async: bcrypt-проверка пароля в отдельном потоке."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_true

from auth.service import hash_password_async, verify_password_async

pytestmark = [pytest.mark.unit, pytest.mark.auth]


class TestVerifyPasswordAsync:
    @autotest.num("2440")
    @autotest.external_id("18052f22-a2f4-4185-8c7e-b731f98465a5")
    @autotest.name("verify_password_async: round-trip с верным/неверным паролем и без хеша")
    async def test_18052f22_verify_password_async_round_trip(self):
        with autotest.step("Arrange: хешируем пароль асинхронно"):
            hashed = await hash_password_async("s3cret")

        with autotest.step("Assert: верный пароль проходит проверку"):
            assert_true(
                await verify_password_async("s3cret", hashed) is True,
                "верный пароль → True",
            )

        with autotest.step("Assert: неверный пароль не проходит проверку"):
            assert_true(
                await verify_password_async("wrong", hashed) is False,
                "неверный пароль → False",
            )

        with autotest.step("Assert: отсутствие хеша → False без исключения"):
            assert_true(
                await verify_password_async("x", None) is False,
                "хеш=None → False",
            )
