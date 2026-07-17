"""Общий экземпляр slowapi Limiter. Вынесен в отдельный модуль ради циклов импорта."""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _rate_limit_key(request: Request) -> str:
    """Ключ на связку user + session. Если пользователь не привязан, используем IP."""
    user = getattr(request.state, "user", None) if hasattr(request, "state") else None
    sid = request.path_params.get("session_id", "unknown")
    if user is None:
        return f"ip:{get_remote_address(request)}:{sid}"
    user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
    return f"user:{user_id}:{sid}"


limiter = Limiter(key_func=_rate_limit_key)


def exchange_rate_limit_key(request: Request) -> str:
    """Ключ лимита для /auth/exchange строится по email субъекта, а не по IP.

    Это доверенный server-to-server вызов из Next BFF, поэтому все запросы идут с
    одного IP. Ключ по IP схлопнул бы всех пользователей в одно глобальное ведро.
    Email кладёт в request.state зависимость _stash_exchange_subject до проверки
    лимита. Неймспейсы user:/ip: разнесены, чтобы fallback не коллизировал.
    """
    subject = getattr(request.state, "exchange_subject", None)
    if subject:
        return f"exchange:user:{subject}"
    return f"exchange:ip:{get_remote_address(request)}"
