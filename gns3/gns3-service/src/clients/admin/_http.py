# Транспортный миксин admin-клиента: аутентификация, refresh, retry.

import asyncio
import base64
import functools
import json
import logging
import time

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


def _is_transient(exc: BaseException) -> bool:
    if isinstance(
        exc, (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.RemoteProtocolError)
    ):
        return True
    if isinstance(exc, httpx.HTTPStatusError) and 500 <= exc.response.status_code < 600:
        return True
    return False


transient_retry = retry(
    retry=retry_if_exception(_is_transient),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4.0),
    reraise=True,
)


def retry_on_401(method):
    """Декоратор: при 401 повторно аутентифицируемся и однократно ретраим."""

    @functools.wraps(method)
    async def wrapper(self, *args, **kwargs):
        try:
            return await method(self, *args, **kwargs)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 401:
                raise
            async with self._refresh_lock:
                logger.warning("Got 401, re-authenticating admin client")
                await self.authenticate()
            return await method(self, *args, **kwargs)

    return wrapper


class HttpMixin:
    """Транспортный миксин: httpx-клиент, JWT, refresh."""

    def _init_http(self, base_url: str, admin_user: str, admin_password: str) -> None:
        self._base_url = base_url
        self._admin_user = admin_user
        self._admin_password = admin_password
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=30,
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=10),
        )
        self.token: str | None = None
        self._refresh_task: asyncio.Task | None = None
        self._refresh_lock = asyncio.Lock()

    def _auth_headers(self) -> dict[str, str]:
        if self.token is None:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def set_admin_token(self, token: str) -> None:
        """Установить admin JWT вручную. Используется тестами для подмены
        authenticate() реальным или фейковым токеном без HTTP-вызова.
        """
        self.token = token

    async def authenticate(self) -> None:
        """Получить admin JWT."""
        response = await self._client.post(
            "/v3/access/users/authenticate",
            json={"username": self._admin_user, "password": self._admin_password},
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]
        self._schedule_refresh()

    def _decode_exp(self, token: str) -> int:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return int(payload["exp"])

    def _schedule_refresh(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
        try:
            exp = self._decode_exp(self.token)
        except Exception:
            logger.warning("Failed to decode JWT exp; reactive 401-retry only")
            return
        now = int(time.time())
        delay = max(60, exp - now - 60)
        logger.info("admin JWT next refresh in %ds", delay)
        self._refresh_task = asyncio.create_task(self._refresh_after(delay))

    async def _refresh_after(self, delay: float) -> None:
        try:
            await asyncio.sleep(delay)
            async with self._refresh_lock:
                await self.authenticate()
            logger.info("admin JWT refreshed proactively")
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Proactive JWT refresh failed; will fall back to reactive 401 retry")

    async def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Универсальный авторизованный запрос к GNS3 admin API.

        Прозрачно подмешивает Authorization, прокидывает остальные kwargs
        в httpx.AsyncClient.request. Не делает raise_for_status — это
        ответственность вызывающего, чтобы тот сам решил, что считать ошибкой.
        """
        headers = kwargs.pop("headers", None) or {}
        merged_headers = {**self._auth_headers(), **headers}
        return await self._client.request(method, path, headers=merged_headers, **kwargs)

    async def close(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
        await self._client.aclose()


# Алиасы для удобства импорта из миксинов-наследников.
_transient_retry = transient_retry
_retry_on_401 = retry_on_401
