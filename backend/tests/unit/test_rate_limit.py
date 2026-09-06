import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from starlette.requests import Request

from kit.rate_limit import (
    credentials_rate_limit_key,
    exchange_rate_limit_key,
    ticket_rate_limit_key,
)

pytestmark = [pytest.mark.unit]


def _request(subject: str | None, client_ip: str = "10.0.0.1", attr: str = "exchange_subject"):
    """Minimal ASGI Request with state and client, for testing key_func."""
    scope = {
        "type": "http",
        "headers": [],
        "client": (client_ip, 0),
        "state": {},
    }
    request = Request(scope)
    if subject is not None:
        setattr(request.state, attr, subject)
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


class TestCredentialsRateLimitKey:
    """/login and /register arrive from the Next BFF, so every caller shares one address."""

    @autotest.num("724")
    @autotest.external_id("5c1f0a92-7b3e-4d81-90a2-6f4c1de83b17")
    @autotest.name("credentials_rate_limit_key: two learners on one address get separate buckets")
    def test_5c1f0a92_distinct_learners_distinct_keys(self):
        with autotest.step("Arrange: two sign-ins relayed from the same BFF address"):
            first = _request("alice@example.com", attr="auth_subject")
            second = _request("bob@example.com", attr="auth_subject")

        with autotest.step("Act: derive a key for each"):
            key_a = credentials_rate_limit_key(first)
            key_b = credentials_rate_limit_key(second)

        with autotest.step("Assert: keyed by learner, so a class does not share one allowance"):
            assert_true(key_a != key_b, "one bucket per learner")
            assert_true("10.0.0.1" not in key_a, "not tied to the relaying address")

    @autotest.num("725")
    @autotest.external_id("9d20b5ac-1e64-42f7-8b0d-2ac7e5f19a34")
    @autotest.name("credentials_rate_limit_key: no email falls back to the address")
    def test_9d20b5ac_fallback_is_the_address(self):
        with autotest.step("Arrange: a request whose body carried no email"):
            request = _request(None)

        with autotest.step("Act: derive the key"):
            key = credentials_rate_limit_key(request)

        with autotest.step("Assert: falls back to the address, in its own namespace"):
            assert_true("10.0.0.1" in key, "fallback uses the address")
            assert_true(key.startswith("credentials:ip:"), "namespaced apart from subject keys")


class TestTicketRateLimitKey:
    """Redeem is bucketed per ticket: every student opening a lab redeems one."""

    @autotest.num("726")
    @autotest.external_id("b7e4318f-05ca-4a6d-9c31-8e2f0d5ab946")
    @autotest.name("ticket_rate_limit_key: two redemptions do not share an allowance")
    def test_b7e4318f_distinct_tickets_distinct_keys(self):
        with autotest.step("Arrange: two students redeeming their own tickets"):
            first = _request("ticket-one", attr="redeem_ticket")
            second = _request("ticket-two", attr="redeem_ticket")

        with autotest.step("Act: derive a key for each"):
            key_a = ticket_rate_limit_key(first)
            key_b = ticket_rate_limit_key(second)

        with autotest.step("Assert: one bucket per ticket, so a cohort opens labs in parallel"):
            assert_true(key_a != key_b, "one bucket per ticket")
            assert_equal(key_a, "ticket:ticket-one", "keyed by the ticket itself")
