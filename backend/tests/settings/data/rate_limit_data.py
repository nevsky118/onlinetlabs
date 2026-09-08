"""Test data for the rate limit key functions."""

from starlette.requests import Request

from config import settings


class RateLimitRequestData:
    """Builds the requests a key function reads."""

    relay_address = "10.0.0.1"
    learner_address = "198.51.100.4"
    other_address = "198.51.100.5"
    learner_email = "alice@example.com"
    other_email = "bob@example.com"
    first_ticket = "ticket-one"
    second_ticket = "ticket-two"

    @classmethod
    def forwarded_from(cls, address: str, **state: str) -> Request:
        """A relayed request carrying the address and the token."""
        return cls._build(address, trusted=True, **state)

    @classmethod
    def spoofed_by(cls, claimed: str, real: str, **state: str) -> Request:
        """A caller value in front of the proxy's own entry."""
        return cls._build(f"{claimed}, {real}", trusted=True, **state)

    @classmethod
    def forged_without_token(cls, address: str, **state: str) -> Request:
        """A claimed address with no token to vouch for it."""
        return cls._build(address, trusted=False, **state)

    @classmethod
    def _build(cls, forwarded: str, trusted: bool, **state: str) -> Request:
        """The Request, with headers and stashed state."""
        headers = [(b"x-forwarded-for", forwarded.encode())]
        if trusted:
            token = settings.security.internal_api_token
            headers.append((b"authorization", f"Bearer {token}".encode()))
        scope = {
            "type": "http",
            "headers": headers,
            "client": (cls.relay_address, 0),
            "state": {},
        }
        request = Request(scope)
        for name, value in state.items():
            setattr(request.state, name, value)
        return request
