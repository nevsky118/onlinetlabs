"""Tests for verify_password_async: bcrypt password check on a separate thread."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_true

from auth.service import hash_password_async, verify_password_async

pytestmark = [pytest.mark.unit, pytest.mark.auth]


class TestVerifyPasswordAsync:
    @autotest.num("2440")
    @autotest.external_id("18052f22-a2f4-4185-8c7e-b731f98465a5")
    @autotest.name(
        "verify_password_async: round-trip with a correct/incorrect password and no hash"
    )
    async def test_18052f22_verify_password_async_round_trip(self):
        with autotest.step("Arrange: hash the password asynchronously"):
            hashed = await hash_password_async("s3cret")

        with autotest.step("Assert: correct password passes verification"):
            assert_true(
                await verify_password_async("s3cret", hashed) is True,
                "correct password → True",
            )

        with autotest.step("Assert: incorrect password fails verification"):
            assert_true(
                await verify_password_async("wrong", hashed) is False,
                "incorrect password → False",
            )

        with autotest.step("Assert: missing hash → False without exception"):
            assert_true(
                await verify_password_async("x", None) is False,
                "hash=None → False",
            )
