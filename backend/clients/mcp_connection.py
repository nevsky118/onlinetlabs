"""A long-lived MCP session, opened and closed inside the task that owns it."""

import asyncio
import logging

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)

CLOSE_TIMEOUT = 5.0


class MCPConnection:
    """One shared MCP session.

    anyio refuses a cancel scope exited from a different task, so the transport
    contexts are entered and left in `_run` and never handed to a caller.
    """

    def __init__(self, mcp_url: str, timeout: float) -> None:
        """Starts the owning task; callers wait on `session`."""
        self._mcp_url = mcp_url
        self._timeout = timeout
        self._session: ClientSession | None = None
        self._error: Exception | None = None
        self._ready = asyncio.Event()
        self._closing = asyncio.Event()
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        """Holds the session open until close, then unwinds it here."""
        try:
            async with (
                streamablehttp_client(self._mcp_url, timeout=self._timeout) as (read, write, _),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                self._session = session
                self._ready.set()
                await self._closing.wait()
        except Exception as exc:
            self._error = exc
        finally:
            self._session = None
            self._ready.set()

    async def session(self) -> ClientSession:
        """The live session, or whatever stopped it from opening."""
        await self._ready.wait()
        if self._session is None:
            raise self._error or ConnectionError("MCP session is closed")
        return self._session

    @property
    def usable(self) -> bool:
        """False once the owning task has finished."""
        return not self._task.done()

    async def close(self) -> None:
        """Asks the owning task to unwind, then stops waiting for it."""
        self._closing.set()
        try:
            await asyncio.wait_for(self._task, timeout=CLOSE_TIMEOUT)
        except TimeoutError:
            logger.warning("MCP connection did not close in %ss", CLOSE_TIMEOUT)
        except Exception:
            logger.warning("MCP connection close failed", exc_info=True)
