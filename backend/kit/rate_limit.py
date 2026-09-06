"""Shared slowapi Limiter instance. Moved into a separate module because of import cycles."""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

# Caddy appends the direct peer to X-Forwarded-For, so the last entry is the
# real caller. Anything a client puts in the header itself sits to its left.
TRUSTED_PROXY_HOPS = 1


def client_ip(request: Request) -> str:
    """The caller's address, trusting exactly one reverse-proxy hop."""
    forwarded = request.headers.get("x-forwarded-for", "") if hasattr(request, "headers") else ""
    parts = [p.strip() for p in forwarded.split(",") if p.strip()]
    if len(parts) >= TRUSTED_PROXY_HOPS:
        return parts[-TRUSTED_PROXY_HOPS]
    return get_remote_address(request)


def _rate_limit_key(request: Request) -> str:
    """Key on the user + session pair. If no user is attached, we use the IP."""
    user = getattr(request.state, "user", None) if hasattr(request, "state") else None
    sid = request.path_params.get("session_id", "unknown")
    if user is None:
        return f"ip:{client_ip(request)}:{sid}"
    user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
    return f"user:{user_id}:{sid}"


limiter = Limiter(key_func=_rate_limit_key)


def exchange_rate_limit_key(request: Request) -> str:
    """The rate limit key for /auth/exchange is built from the subject's email, not from the IP.

    This is a trusted server-to-server call from the Next BFF, so every request comes
    from the same IP. An IP-based key would collapse all users into one global bucket.
    The email is put into request.state by the _stash_exchange_subject dependency before
    the limit check. The user:/ip: namespaces are kept apart so the fallback cannot collide.
    """
    subject = getattr(request.state, "exchange_subject", None)
    if subject:
        return f"exchange:user:{subject}"
    return f"exchange:ip:{client_ip(request)}"


def credentials_rate_limit_key(request: Request) -> str:
    """The rate limit key for /auth/login and /auth/register, keyed by email.

    These reach the backend the same way /auth/exchange does: server-side from the
    Next BFF, every request carrying the dashboard container's address. Keyed by IP
    they would share one bucket, so a class signing in together would spend the whole
    per-minute allowance on the first few students and the rest would see 429.
    The email is stashed on request.state by _stash_credentials_subject before the
    limit is evaluated.
    """
    subject = getattr(request.state, "auth_subject", None)
    if subject:
        return f"credentials:user:{subject}"
    return f"credentials:ip:{client_ip(request)}"


def ticket_rate_limit_key(request: Request) -> str:
    """The rate limit key for /gns3/redeem, keyed by the ticket being redeemed.

    Same BFF path, same collapse into one bucket if keyed by IP, and here the ceiling
    is reached by ordinary use: every student opening a lab redeems a ticket.
    Guessing is not what the limit defends against anyway, a ticket is 256 bits and
    single-use, so the bucket is per ticket: one ticket cannot be hammered, and
    students no longer queue behind each other.
    """
    ticket = getattr(request.state, "redeem_ticket", None)
    if ticket:
        return f"ticket:{ticket}"
    return f"ticket:ip:{client_ip(request)}"
