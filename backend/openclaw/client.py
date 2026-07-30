"""HTTP client for the OpenClaw Gateway."""

import time
from dataclasses import dataclass, field

import httpx


@dataclass
class OpenClawCompletion:
    """Normalized OpenClaw generation result."""

    success: bool
    content: str
    model: str | None = None
    provider: str = "openclaw"
    latency_ms: int | None = None
    usage: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None


class OpenClawClient:
    """Minimal OpenAI-compatible client for the OpenClaw Gateway."""

    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        model: str = "openclaw",
        timeout_seconds: float = 30.0,
    ):
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout_seconds,
            headers=self._build_headers(),
        )

    async def __aenter__(self) -> "OpenClawClient":
        """Returns the client for use in async with."""
        return self

    async def __aexit__(self, *_) -> None:
        """Closes the HTTP client on exit from async with."""
        await self.aclose()

    async def aclose(self) -> None:
        """Closes the OpenClaw HTTP client's connection pool."""
        await self._client.aclose()

    async def complete(self, messages: list[dict]) -> OpenClawCompletion:
        """Calls /v1/chat/completions and normalizes the response."""
        started = time.perf_counter()
        payload = {"model": self._model, "messages": messages, "stream": False}

        try:
            response = await self._post(payload)
            latency_ms = int((time.perf_counter() - started) * 1000)
        except httpx.TimeoutException as e:
            return self._error("openclaw_timeout", str(e), started)
        except httpx.RequestError as e:
            return self._error("openclaw_unreachable", str(e), started)

        if response.status_code >= 400:
            return OpenClawCompletion(
                success=False,
                content="",
                model=self._model,
                latency_ms=latency_ms,
                error_code="openclaw_unreachable",
                error_message=f"HTTP {response.status_code}: {response.text}",
            )

        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as e:
            return OpenClawCompletion(
                success=False,
                content="",
                model=self._model,
                latency_ms=latency_ms,
                raw=response.json() if _looks_like_json(response) else {},
                error_code="openclaw_invalid_response",
                error_message=str(e),
            )

        if not content:
            return OpenClawCompletion(
                success=False,
                content="",
                model=body.get("model", self._model),
                latency_ms=latency_ms,
                raw=body,
                error_code="openclaw_empty_response",
                error_message="empty assistant content",
            )

        return OpenClawCompletion(
            success=True,
            content=content,
            model=body.get("model", self._model),
            latency_ms=latency_ms,
            usage=body.get("usage") or {},
            raw=body,
        )

    async def _post(self, payload: dict) -> httpx.Response:
        """Sends the request through the long-lived HTTP client."""
        return await self._client.post("/v1/chat/completions", json=payload)

    def _build_headers(self) -> dict:
        """Builds the persistent headers for the OpenClaw Gateway."""
        if not self._token:
            return {}
        return {"Authorization": f"Bearer {self._token}"}

    def _error(self, code: str, message: str, started: float) -> OpenClawCompletion:
        """Builds an unsuccessful result for transport errors."""
        return OpenClawCompletion(
            success=False,
            content="",
            model=self._model,
            latency_ms=int((time.perf_counter() - started) * 1000),
            error_code=code,
            error_message=message,
        )


def _looks_like_json(response: httpx.Response) -> bool:
    """Returns True if the response body parses as JSON."""
    try:
        response.json()
    except ValueError:
        return False
    return True
