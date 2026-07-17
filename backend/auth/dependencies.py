import logging
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()

# Короткое окно. Токен обновляется фронтом через /auth/exchange перед каждым запросом.
TOKEN_EXPIRE_MINUTES = 5


def may_select_model(role: str, can_select_model: bool | None, selectable_roles: set[str]) -> bool:
    """Право на выбор модели: per-user тоггл важнее, иначе роль-дефолт."""
    if can_select_model is not None:
        return can_select_model
    return role in selectable_roles


def may_view_agent_logs(
    role: str, can_view_agent_logs: bool | None, viewer_roles: set[str]
) -> bool:
    """Право видеть лог агентов: per-user тоггл важнее, иначе роль-дефолт."""
    if can_view_agent_logs is not None:
        return can_view_agent_logs
    return role in viewer_roles


def can_view_session_activity(user: dict, session) -> bool:
    """Видит ли пользователь активность данной сессии."""
    if not user.get("can_view_logs"):
        return False
    return session.user_id == user["id"] or user.get("role") in ("instructor", "admin")


def create_backend_token(
    user_id: str,
    role: str,
    can_select: bool = False,
    can_view_logs: bool = False,
    is_active: bool = False,
) -> str:
    """Выдать HS256 JWT с claims sub, role, can_select, can_view_logs, is_active, время жизни 5 минут."""
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "role": role,
        "can_select": can_select,
        "can_view_logs": can_view_logs,
        "is_active": is_active,
        "exp": now + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
        "iat": now,
    }
    return jwt.encode(payload, settings.api.jwt_secret, algorithm="HS256")


def decode_backend_token(token: str, secret: str) -> dict:
    """Декодировать и проверить HS256 JWT."""
    return jwt.decode(token, secret, algorithms=["HS256"])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """FastAPI зависимость. Извлекает пользователя из backend JWT."""
    try:
        payload = decode_backend_token(credentials.credentials, settings.api.jwt_secret)
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return {
            "id": user_id,
            "role": role,
            "can_select": bool(payload.get("can_select")),
            "can_view_logs": bool(payload.get("can_view_logs")),
            "is_active": bool(payload.get("is_active")),
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
) -> dict | None:
    """FastAPI зависимость. Возвращает пользователя из JWT или None без ошибки."""
    if credentials is None:
        return None
    try:
        payload = decode_backend_token(credentials.credentials, settings.api.jwt_secret)
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None:
            return None
        return {
            "id": user_id,
            "role": role,
            "can_select": bool(payload.get("can_select")),
            "can_view_logs": bool(payload.get("can_view_logs")),
            "is_active": bool(payload.get("is_active")),
        }
    except JWTError:
        return None


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """FastAPI зависимость. Пропускает только роль admin."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user


def require_instructor(current_user: dict = Depends(get_current_user)) -> dict:
    """FastAPI зависимость. Пропускает преподавателя или админа.

    Используется для кабинета преподавателя: просмотр прогресса учеников
    доступен ролям instructor и admin, но не student.
    """
    if current_user.get("role") not in ("instructor", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Instructor only")
    return current_user


def require_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Пропускает только активированных пользователей. Иначе 403."""
    if not current_user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт не активирован")
    return current_user


def require_internal_caller(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> None:
    """Авторизует server-to-server вызовы (Next.js в backend /auth/exchange).

    Сверяет Authorization Bearer INTERNAL_API_TOKEN с общим секретом. При
    несовпадении возвращает 401, поэтому утёкший client-side вызов не сможет
    выдать backend JWT. Тот же токен используется на канале backend gns3-service.
    """
    expected = settings.security.internal_api_token
    if not expected or not secrets.compare_digest(credentials.credentials, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal token",
        )


async def verify_jwt_for_ws(token: str | None) -> dict | None:
    """Проверяет JWT и возвращает пользователя или None при ошибке. Для WS-хендлеров."""
    if not token:
        return None
    try:
        payload = decode_backend_token(token, settings.api.jwt_secret)
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None:
            return None
        return {
            "id": user_id,
            "role": role,
            "can_select": bool(payload.get("can_select")),
            "can_view_logs": bool(payload.get("can_view_logs")),
            "is_active": bool(payload.get("is_active")),
        }
    except JWTError as exc:
        logger.warning("ws jwt verify failed", extra={"error": str(exc)})
        return None
