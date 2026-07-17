import pytest
from starlette.requests import Request
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from rate_limit import exchange_rate_limit_key

pytestmark = [pytest.mark.unit]


def _request(subject: str | None, client_ip: str = "10.0.0.1") -> Request:
    """Минимальный ASGI Request с state и client, для проверки key_func."""
    scope = {
        "type": "http",
        "headers": [],
        "client": (client_ip, 0),
        "state": {},
    }
    request = Request(scope)
    if subject is not None:
        request.state.exchange_subject = subject
    return request


class TestExchangeRateLimitKey:
    @autotest.num("720")
    @autotest.external_id("d4e5f607-0809-4a1b-8c23-567890abcdef")
    @autotest.name("exchange_rate_limit_key: ключ по email субъекта, не по IP")
    def test_d4e5f607_key_uses_subject_email(self):
        with autotest.step("Act: ключ для запроса с exchange_subject"):
            key = exchange_rate_limit_key(_request("alice@example.com"))

        with autotest.step("Assert: ключ содержит email, а не IP"):
            assert_true("alice@example.com" in key, "ключ содержит email")
            assert_true("10.0.0.1" not in key, "ключ не привязан к IP")

    @autotest.num("721")
    @autotest.external_id("e5f60708-090a-4b2c-8d34-67890abcdef0")
    @autotest.name("exchange_rate_limit_key: разные юзеры → разные вёдра")
    def test_e5f60708_distinct_users_distinct_keys(self):
        with autotest.step("Act: ключи двух разных юзеров с одного IP"):
            key_a = exchange_rate_limit_key(_request("a@example.com"))
            key_b = exchange_rate_limit_key(_request("b@example.com"))

        with autotest.step("Assert: ключи различаются (нет глобального ведра)"):
            assert_true(key_a != key_b, "ключи разных юзеров не совпадают")

    @autotest.num("722")
    @autotest.external_id("f6070809-0a0b-4c3d-8e45-7890abcdef01")
    @autotest.name("exchange_rate_limit_key: один юзер → стабильный ключ")
    def test_f6070809_same_user_stable_key(self):
        with autotest.step("Act: ключ одного юзера дважды"):
            first = exchange_rate_limit_key(_request("same@example.com"))
            second = exchange_rate_limit_key(_request("same@example.com"))

        with autotest.step("Assert: ключ стабилен"):
            assert_equal(first, second, "один юзер — один ключ")

    @autotest.num("723")
    @autotest.external_id("07080910-0b0c-4d4e-8f56-890abcdef012")
    @autotest.name(
        "exchange_rate_limit_key: без субъекта → fallback на IP, не путается с email-ключами"
    )
    def test_07080910_fallback_ip_distinct_from_subject(self):
        with autotest.step("Act: ключ без exchange_subject"):
            ip_key = exchange_rate_limit_key(_request(None, client_ip="10.0.0.1"))
            subject_key = exchange_rate_limit_key(_request("10.0.0.1"))

        with autotest.step("Assert: fallback по IP не коллизирует с email-ключом того же текста"):
            assert_true("10.0.0.1" in ip_key, "fallback использует IP")
            assert_true(ip_key != subject_key, "IP-ключ и email-ключ разнесены неймспейсами")
