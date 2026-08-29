import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from starlette.requests import Request

from kit.rate_limit import exchange_rate_limit_key

pytestmark = [pytest.mark.unit]


def _request(subject: str | None, client_ip: str = "10.0.0.1") -> Request:
    """Minimal ASGI Request with state and client, for testing key_func."""
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
    @autotest.external_id("3ab9ff65-e172-4c35-8bfd-9957ef920e43")
    @autotest.name("exchange_rate_limit_key: key is by subject email, not by IP")
    def test_3ab9ff65_key_uses_subject_email(self):
        with autotest.step("Act: key for a request with exchange_subject"):
            key = exchange_rate_limit_key(_request("alice@example.com"))

        with autotest.step("Assert: key contains the email, not the IP"):
            assert_true("alice@example.com" in key, "key contains email")
            assert_true("10.0.0.1" not in key, "key not tied to IP")

    @autotest.num("721")
    @autotest.external_id("cfffd483-3120-4c56-9092-cbbd212dc95f")
    @autotest.name("exchange_rate_limit_key: distinct users → distinct buckets")
    def test_cfffd483_distinct_users_distinct_keys(self):
        with autotest.step("Act: keys for two different users on the same IP"):
            key_a = exchange_rate_limit_key(_request("a@example.com"))
            key_b = exchange_rate_limit_key(_request("b@example.com"))

        with autotest.step("Assert: keys differ (no global bucket)"):
            assert_true(key_a != key_b, "different users don't share a key")

    @autotest.num("722")
    @autotest.external_id("ff0bd12b-2448-4469-af79-c53b6371b02a")
    @autotest.name("exchange_rate_limit_key: same user → stable key")
    def test_ff0bd12b_same_user_stable_key(self):
        with autotest.step("Act: key for the same user twice"):
            first = exchange_rate_limit_key(_request("same@example.com"))
            second = exchange_rate_limit_key(_request("same@example.com"))

        with autotest.step("Assert: key is stable"):
            assert_equal(first, second, "one user, one key")

    @autotest.num("723")
    @autotest.external_id("07080910-0b0c-4d4e-8f56-890abcdef012")
    @autotest.name(
        "exchange_rate_limit_key: no subject → falls back to IP, not confused with email keys"
    )
    def test_07080910_fallback_ip_distinct_from_subject(self):
        with autotest.step("Act: key without exchange_subject"):
            ip_key = exchange_rate_limit_key(_request(None, client_ip="10.0.0.1"))
            subject_key = exchange_rate_limit_key(_request("10.0.0.1"))

        with autotest.step(
            "Assert: IP fallback doesn't collide with an email key of the same text"
        ):
            assert_true("10.0.0.1" in ip_key, "fallback uses IP")
            assert_true(ip_key != subject_key, "IP key and email key live in separate namespaces")
