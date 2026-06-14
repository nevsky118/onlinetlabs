import logging
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()

# Короткое окно. Токен обновляется фронтом через /auth/exchange перед каждым запросом.
TOKEN_EXPIRE_MINUTES = 5


def create_backend_token(user_id: str, role: str) -> str:
    """Выдать HS256 JWT с claims sub и role, время жизни 5 минут."""
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc),
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        return {"id": user_id, "role": role}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        HTTPBearer(auto_error=False)
    ),
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
        return {"id": user_id, "role": role}
    except JWTError:
        return None


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """FastAPI зависимость. Пропускает только роль admin."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin only"
        )
    return current_user


def require_instructor(current_user: dict = Depends(get_current_user)) -> dict:
    """FastAPI зависимость. Пропускает преподавателя или админа.

    Используется для кабинета преподавателя: просмотр прогресса учеников
    доступен ролям instructor и admin, но не student.
    """
    if current_user.get("role") not in ("instructor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Instructor only"
        )
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
    if not expected or credentials.credentials != expected:
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
        return {"id": user_id, "role": role}
    except JWTError as exc:
        logger.warning("ws jwt verify failed", extra={"error": str(exc)})
        return None
