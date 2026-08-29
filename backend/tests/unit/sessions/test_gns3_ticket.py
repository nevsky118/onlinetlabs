"""One-time GNS3 tickets: the password must never reach the browser."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from sessions.schemas import CredentialsResponse, LaunchResponse
from sessions.services.proxy import existing_gns3_deep_url
from sessions.services.ticket import TicketStore

pytestmark = [pytest.mark.unit]

_SESSION = "sess-ticket-1"
_OWNER = "user-ticket-1"


class FakeTicketRedis:
    """The two redis commands the ticket store uses."""

    def __init__(self):
        self.values: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        """Stores a value with its expiry."""
        self.values[key] = value
        if ex is not None:
            self.ttls[key] = ex

    async def getdel(self, key: str) -> str | None:
        """Reads and removes in one step, which is what makes a ticket single-use."""
        return self.values.pop(key, None)


class TestTicketStore:
    """A ticket answers once, and only once."""

    @autotest.num("3436")
    @autotest.external_id("411f6d32-b39a-4e20-ac2f-947e88faf888")
    @autotest.name("ticket: redeems once and is then unknown")
    async def test_411f6d32_single_use(self):
        with autotest.step("Arrange: an issued ticket"):
            store = TicketStore(redis=FakeTicketRedis())
            ticket = await store.issue(_SESSION, _OWNER)

        with autotest.step("Act: redeem it twice"):
            first = await store.redeem(ticket)
            second = await store.redeem(ticket)

        with autotest.step("Assert: the second attempt gets nothing"):
            assert_equal(first, {"session_id": _SESSION, "user_id": _OWNER}, "payload")
            assert_true(second is None, "already used")

    @autotest.num("3437")
    @autotest.external_id("2b3b05c2-e4e1-4eda-91e1-c6860ecd61e8")
    @autotest.name("ticket: carries an expiry and is not guessable")
    async def test_2b3b05c2_expiry_and_entropy(self):
        with autotest.step("Arrange: an issued ticket"):
            redis = FakeTicketRedis()
            store = TicketStore(redis=redis)
            ticket = await store.issue(_SESSION, _OWNER)

        with autotest.step("Act: read what was stored"):
            ttl = next(iter(redis.ttls.values()))

        with autotest.step("Assert: short-lived, and long enough to resist guessing"):
            assert_true(0 < ttl <= 300, "short ttl")
            assert_true(len(ticket) >= 40, "high entropy")

    @autotest.num("3438")
    @autotest.external_id("b3db42d4-aa38-47cf-a5d1-fdf7fbfddec9")
    @autotest.name("ticket: an unknown value redeems to nothing")
    async def test_b3db42d4_unknown_ticket(self):
        with autotest.step("Arrange: an empty store"):
            store = TicketStore(redis=FakeTicketRedis())

        with autotest.step("Act: redeem a value that was never issued"):
            result = await store.redeem("not-a-ticket")

        with autotest.step("Assert: nothing"):
            assert_true(result is None, "unknown ticket")

    @autotest.num("3439")
    @autotest.external_id("7d5eb597-74aa-45cf-a973-409973e2ce82")
    @autotest.name("ticket: an empty value is rejected without touching redis")
    async def test_7d5eb597_empty_ticket(self):
        with autotest.step("Arrange: a redis that would fail if called"):
            redis = FakeTicketRedis()
            redis.getdel = AsyncMock(side_effect=AssertionError("must not be called"))
            store = TicketStore(redis=redis)

        with autotest.step("Act: redeem an empty string"):
            result = await store.redeem("")

        with autotest.step("Assert: rejected up front"):
            assert_true(result is None, "empty rejected")


class TestNoPasswordLeaves:
    """The response shapes must not be able to carry a password."""

    @autotest.num("3440")
    @autotest.external_id("b5887a53-c091-4f50-a6a8-062f7627d8b9")
    @autotest.name("responses: neither launch nor credentials expose a password field")
    def test_b5887a53_no_password_field(self):
        with autotest.step("Act: read the declared fields"):
            launch_fields = set(LaunchResponse.model_fields)
            creds_fields = set(CredentialsResponse.model_fields)

        with autotest.step("Assert: no password anywhere"):
            assert_true("gns3_password" not in launch_fields, "launch has no password")
            assert_true("gns3_password" not in creds_fields, "credentials have no password")

    @autotest.num("3441")
    @autotest.external_id("3e765365-3ad3-4c31-8955-7593d2ae7bac")
    @autotest.name("deep link: carries a ticket, never a credential")
    def test_3e765365_deep_link_carries_ticket(self):
        with autotest.step("Arrange: a session with a project and a minted ticket"):
            session = SimpleNamespace(
                id=_SESSION,
                meta={
                    "gns3_project_id": "proj-1",
                    "gns3_username": "student-abc",
                    "enc_password": "encrypted",
                },
            )

        with autotest.step("Act: build the deep link"):
            url = existing_gns3_deep_url(session, "tkt-xyz")

        with autotest.step("Assert: the ticket is in the link and nothing else is"):
            assert_true("ticket=tkt-xyz" in url, "ticket present")
            assert_true("password" not in url, "no password")
            assert_true("username" not in url, "no username")
