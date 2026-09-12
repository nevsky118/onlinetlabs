"""Transparent, unauthenticated WS proxy to the node console."""

from __future__ import annotations

import asyncio
import logging
import uuid

import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

_UPSTREAM_PING_INTERVAL = 20
_UPSTREAM_PING_TIMEOUT = 20

# Bounds the capture lookup.
_SESSION_LOOKUP_TIMEOUT_SEC = 1.0


def parse_console_path(path: str) -> tuple[str, str] | None:
    """Returns (project_id, node_id) for a console WS path, or None."""
    parts = [segment for segment in path.split("/") if segment]
    if len(parts) < 5 or parts[-1] != "ws" or parts[-2] != "console" or parts[-4] != "nodes":
        return None
    node_id = parts[-3]
    try:
        project_index = parts.index("projects")
    except ValueError:
        return None
    if project_index + 1 >= len(parts):
        return None
    return parts[project_index + 1], node_id


def _upstream_url(websocket: WebSocket) -> str:
    """Rebuilds the same URL against the internal gns3-server, query included."""
    base = settings.gns3.url.replace("http://", "ws://").replace("https://", "wss://")
    query = websocket.url.query
    return f"{base.rstrip('/')}{websocket.url.path}" + (f"?{query}" if query else "")


async def _resolve_session(app, project_id: str) -> uuid.UUID | None:
    """Newest non-closed lab session owning this GNS3 project."""
    db_factory = getattr(app.state, "db_factory", None)
    if db_factory is None:
        return None
    from sqlalchemy import select

    from src.db.models import Session as SessionModel
    from src.db.models import SessionStatus

    async with db_factory() as db:
        result = await db.execute(
            select(SessionModel.id)
            .where(
                SessionModel.gns3_project_id == project_id,
                SessionModel.status != SessionStatus.CLOSED,
            )
            .order_by(SessionModel.created_at.desc())
            .limit(2)
        )
        rows = list(result.scalars())
    if len(rows) > 1:
        logger.warning(
            "console proxy: project %s has %d non-closed sessions, using the newest",
            project_id,
            len(rows),
        )
    return rows[0] if rows else None


async def _make_tap(websocket: WebSocket, project_id: str, node_id: str):
    """Builds a tap for this socket, or None."""
    capture = getattr(websocket.app.state, "console_capture", None)
    if capture is None:
        return None
    try:
        session_id = await asyncio.wait_for(
            _resolve_session(websocket.app, project_id), _SESSION_LOOKUP_TIMEOUT_SEC
        )
    except TimeoutError:
        logger.warning(
            "console proxy: session lookup timed out for project %s, capture off", project_id
        )
        return None
    except Exception:
        logger.exception("console proxy: session lookup failed for project %s", project_id)
        return None
    if session_id is None:
        logger.warning("console proxy: no session for project %s, capture off", project_id)
        return None
    return capture.tap(session_id, node_id)


@router.websocket("/v3/{rest:path}")
async def console_ws(websocket: WebSocket, rest: str) -> None:
    """Relays one console socket to gns3-server, recording both directions."""
    parsed = parse_console_path(websocket.url.path)
    if parsed is None:
        # Anything else is misrouted.
        await websocket.close(code=4404)
        return
    project_id, node_id = parsed

    # Connect upstream before accepting.
    subprotocols = websocket.scope.get("subprotocols") or []
    try:
        upstream = await websockets.connect(
            _upstream_url(websocket),
            subprotocols=subprotocols or None,
            ping_interval=_UPSTREAM_PING_INTERVAL,
            ping_timeout=_UPSTREAM_PING_TIMEOUT,
            max_size=None,
        )
    except Exception as exc:
        logger.warning("console proxy: upstream refused node %s: %s", node_id, exc)
        await websocket.close(code=1011)
        return

    tap = await _make_tap(websocket, project_id, node_id)
    await websocket.accept(subprotocol=upstream.subprotocol)

    async def client_to_upstream() -> None:
        """What the learner types."""
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                return
            data = message.get("bytes")
            if data is None:
                text = message.get("text") or ""
                await upstream.send(text)
                data = text.encode("utf-8", errors="replace")
            else:
                await upstream.send(data)
            if tap is not None:
                tap.from_client(data)

    async def upstream_to_client() -> None:
        """What the node answers."""
        async for raw in upstream:
            if isinstance(raw, str):
                await websocket.send_text(raw)
                data = raw.encode("utf-8", errors="replace")
            else:
                data = raw
                await websocket.send_bytes(raw)
            if tap is not None:
                tap.from_node(data)

    client_to_upstream_task = asyncio.create_task(client_to_upstream())
    upstream_to_client_task = asyncio.create_task(upstream_to_client())
    pumps = {client_to_upstream_task, upstream_to_client_task}
    try:
        done, pending = await asyncio.wait(pumps, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            try:
                task.result()
            except WebSocketDisconnect:
                pass
            except Exception:
                logger.debug("console proxy: relay for node %s ended", node_id, exc_info=True)
    finally:
        for task in pumps:
            task.cancel()
        for task in pumps:
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.debug("console proxy: pump for node %s failed", node_id, exc_info=True)
        if tap is not None:
            tap.close()
        for closer in (upstream.close, websocket.close):
            try:
                await closer()
            except Exception:
                pass
