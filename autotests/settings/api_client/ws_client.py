"""Async WS client для autotests."""

import asyncio
import json

import websockets


class WSClient:
    def __init__(self, base_url: str, token: str | None = None):
        self._base_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
        self._token = token

    async def connect(self, path: str, timeout: float = 10.0):
        """Open WS connection. Returns a websockets.WebSocketClientProtocol context manager."""
        url = f"{self._base_url}{path}"
        if self._token:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}token={self._token}"
        return await websockets.connect(url, open_timeout=timeout)

    async def recv_json(self, ws, timeout: float = 10.0) -> dict:
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
        return json.loads(raw)
