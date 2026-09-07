import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from starlette.requests import Request

from kit.rate_limit import (
    address_rate_limit_key,
    credentials_rate_limit_key,
    exchange_rate_limit_key,
)
from tests.settings.data.rate_limit_data import RateLimitRequestData

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
    """Login buckets pair the address with the account."""

    @autotest.num("3503")
    @autotest.external_id("77052dff-4715-4a5d-8883-58e9124a4081")
    @autotest.name("credentials_rate_limit_key: two learners on one address get separate buckets")
    def test_77052dff_distinct_learners_distinct_keys(self):
        with autotest.step("Arrange: two sign-ins from one classroom address"):
            first = RateLimitRequestData.forwarded_from(
                RateLimitRequestData.learner_address,
                auth_subject=RateLimitRequestData.learner_email,
            )
            second = RateLimitRequestData.forwarded_from(
                RateLimitRequestData.learner_address,
                auth_subject=RateLimitRequestData.other_email,
            )

        with autotest.step("Act: derive a key for each"):
            key_a = credentials_rate_limit_key(first)
            key_b = credentials_rate_limit_key(second)

        with autotest.step("Assert: a cohort behind one address does not share an allowance"):
            assert_true(key_a != key_b, "one bucket per learner")
            assert_true(
                RateLimitRequestData.relay_address not in key_a,
                "keyed on the learner's address, not the relaying container",
            )

    @autotest.num("3504")
    @autotest.external_id("3c8ab547-6ef2-4382-9383-97c8289332ad")
    @autotest.name("credentials_rate_limit_key: one account from two addresses gets two buckets")
    def test_3c8ab547_same_account_distinct_addresses(self):
        with autotest.step("Arrange: the same email tried from the owner's address and another"):
            owner = RateLimitRequestData.forwarded_from(
                RateLimitRequestData.learner_address,
                auth_subject=RateLimitRequestData.learner_email,
            )
            stranger = RateLimitRequestData.forwarded_from(
                RateLimitRequestData.other_address,
                auth_subject=RateLimitRequestData.learner_email,
            )

        with autotest.step("Act: derive a key for each"):
            owner_key = credentials_rate_limit_key(owner)
            stranger_key = credentials_rate_limit_key(stranger)

        with autotest.step("Assert: nobody can spend an account's allowance from elsewhere"):
            assert_true(
                owner_key != stranger_key,
                "the email alone is not the bucket, so the owner cannot be locked out",
            )

    @autotest.num("3505")
    @autotest.external_id("4894f4dc-364d-4df1-aa89-8b0b146b56e1")
    @autotest.name("credentials_rate_limit_key: a body with no email still keys on the address")
    def test_4894f4dc_missing_email_still_bounded(self):
        with autotest.step("Arrange: two requests from one address whose body carried no email"):
            first = RateLimitRequestData.forwarded_from(RateLimitRequestData.learner_address)
            second = RateLimitRequestData.forwarded_from(RateLimitRequestData.learner_address)

        with autotest.step("Act: derive a key for each"):
            first_key = credentials_rate_limit_key(first)
            second_key = credentials_rate_limit_key(second)

        with autotest.step("Assert: one bucket, so a malformed body cannot dodge the limit"):
            assert_equal(first_key, second_key, "same address, same bucket")
            assert_true(
                RateLimitRequestData.learner_address in first_key, "the address carries the key"
            )


class TestAddressRateLimitKey:
    """Sign-up and redeem bucket on the address alone."""

    @autotest.num("3506")
    @autotest.external_id("f85200b1-4268-4ad5-9743-b0d95cea56af")
    @autotest.name("address_rate_limit_key: two addresses get separate buckets")
    def test_f85200b1_distinct_addresses_distinct_keys(self):
        with autotest.step("Arrange: two learners arriving from their own addresses"):
            first = RateLimitRequestData.forwarded_from(RateLimitRequestData.learner_address)
            second = RateLimitRequestData.forwarded_from(RateLimitRequestData.other_address)

        with autotest.step("Act: derive a key for each"):
            key_a = address_rate_limit_key(first)
            key_b = address_rate_limit_key(second)

        with autotest.step("Assert: one caller's traffic does not spend another's allowance"):
            assert_true(key_a != key_b, "one bucket per address")

    @autotest.num("3507")
    @autotest.external_id("94468ec3-86f2-44aa-8c41-58054f24db53")
    @autotest.name("address_rate_limit_key: a fresh ticket or email does not mint a fresh bucket")
    def test_94468ec3_caller_chosen_values_share_one_bucket(self):
        with autotest.step("Arrange: one address redeeming two different tickets"):
            first = RateLimitRequestData.forwarded_from(
                RateLimitRequestData.learner_address,
                redeem_ticket=RateLimitRequestData.first_ticket,
            )
            second = RateLimitRequestData.forwarded_from(
                RateLimitRequestData.learner_address,
                redeem_ticket=RateLimitRequestData.second_ticket,
            )

        with autotest.step("Act: derive a key for each"):
            key_a = address_rate_limit_key(first)
            key_b = address_rate_limit_key(second)

        with autotest.step("Assert: guessing tickets stays metered instead of unbounded"):
            assert_equal(key_a, key_b, "the ticket does not enter the key")

    @autotest.num("3508")
    @autotest.external_id("c82b9880-5309-4445-8e5f-c9e93280d437")
    @autotest.name("address_rate_limit_key: a caller-supplied address does not shift the bucket")
    def test_c82b9880_spoofed_address_ignored(self):
        with autotest.step("Arrange: a caller that put its own value in front of the real one"):
            spoofed = RateLimitRequestData.spoofed_by(
                claimed="203.0.113.9", real=RateLimitRequestData.learner_address
            )
            honest = RateLimitRequestData.forwarded_from(RateLimitRequestData.learner_address)

        with autotest.step("Act: derive a key for each"):
            spoofed_key = address_rate_limit_key(spoofed)
            honest_key = address_rate_limit_key(honest)

        with autotest.step("Assert: the appended entry wins, so the bucket cannot be reset"):
            assert_equal(spoofed_key, honest_key, "only the proxy's own entry is trusted")

    @autotest.num("3512")
    @autotest.external_id("5db89d31-5ea4-4794-be5c-d4d2bb29ce1f")
    @autotest.name("address_rate_limit_key: a forwarded address without the token is ignored")
    def test_5db89d31_untrusted_forward_falls_back_to_peer(self):
        with autotest.step("Arrange: two callers with no token, each claiming its own address"):
            first = RateLimitRequestData.forged_without_token(RateLimitRequestData.learner_address)
            second = RateLimitRequestData.forged_without_token(RateLimitRequestData.other_address)

        with autotest.step("Act: derive a key for each"):
            first_key = address_rate_limit_key(first)
            second_key = address_rate_limit_key(second)

        with autotest.step("Assert: both fall back to the peer, so forging wins no allowance"):
            assert_equal(first_key, second_key, "the claimed address is not believed")
            assert_true(
                RateLimitRequestData.relay_address in first_key, "keyed by the address it dialled"
            )
