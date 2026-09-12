"""Captures console traffic without blocking the proxy."""

from __future__ import annotations

import asyncio
import logging
import re
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from src.console_reconstruct import ConsoleReconstructor

logger = logging.getLogger(__name__)

# Caps one console frame.
MAX_CHUNK_BYTES = 64 * 1024

# Per-connection byte budget.
MAX_CONNECTION_BYTES = 8 * 1024 * 1024

# Per-connection row budget.
MAX_CONNECTION_ROWS = 20_000

# Backlog byte budget.
MAX_QUEUE_BYTES = 64 * 1024 * 1024

# Matches ConsoleCommand.prompt.
MAX_PROMPT_CHARS = 255

# Matches ConsoleChunk/ConsoleCommand.node_id.
MAX_NODE_ID_CHARS = 64

# Password prompt at tail end.
_PASSWORD_PROMPT_RE = re.compile(rb"assword[^\S\r\n]*:[^\S\r\n]*\Z", re.IGNORECASE)

# Keyword, separators, then the rest of the line.
_SECRET_ARG_RE = re.compile(
    rb"(?i)("
    rb"\b(?:secret|password|passwd|key-string|pre-shared-key|authentication-key"
    rb"|key(?![^\S\r\n]+(?:chain|generate|zeroize|config-key|pair|exchange"
    rb"|pubkey-chain|to|id|is)(?=\s|\Z))"
    rb"|community|psk|passphrase|auth|priv)\b"
    rb"(?:[^\S\r\n]|[:=])+"
    rb")[^\r\n]+"
)

# Tail kept for prompt matching.
_TAIL_BYTES = 64

# Max keypress-to-echo delay.
_LEARNER_ENTER_WINDOW = timedelta(seconds=2.0)

_MAX_PENDING_ENTERS = 256

# Enter key bytes.
CR = bytes([13])
LF = bytes([10])


@dataclass(slots=True)
class ConsoleCommandRecord:
    """One reconstructed command on its way to the database."""

    session_id: uuid.UUID
    node_id: str
    connection_id: uuid.UUID
    seq: int
    prompt: str | None
    command: str
    response: str
    ts: datetime
    duration_ms: float | None


@dataclass(slots=True)
class ConsoleFrame:
    """One frame on its way to the database."""

    session_id: uuid.UUID
    node_id: str
    connection_id: uuid.UUID
    seq: int
    direction: str
    payload: bytes
    truncated: bool
    redacted: bool
    ts: datetime


@dataclass(slots=True)
class _DirectionBuffer:
    """Bytes of one direction awaiting a line break."""

    data: bytearray = field(default_factory=bytearray)
    ts: datetime | None = None


def redact_secrets(data: bytes) -> tuple[bytes, bool]:
    """Replaces credential arguments with stars."""
    redacted = _SECRET_ARG_RE.sub(rb"\1***", data)
    return redacted, redacted != data


def _frame_bytes(item: ConsoleFrame | ConsoleCommandRecord) -> int:
    """Rough resident size of one queued item."""
    if isinstance(item, ConsoleFrame):
        return len(item.payload)
    return len(item.command) + len(item.response)


class ConsoleCapture:
    """Queue plus a background flusher writing console frames in batches."""

    def __init__(
        self,
        db_factory,
        *,
        queue_size: int = 10_000,
        max_queue_bytes: int = MAX_QUEUE_BYTES,
        batch_size: int = 200,
        flush_interval: float = 1.0,
    ) -> None:
        self._db_factory = db_factory
        self._queue: asyncio.Queue[ConsoleFrame | ConsoleCommandRecord] = asyncio.Queue(
            maxsize=queue_size
        )
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._task: asyncio.Task | None = None
        self._dropped = 0
        self._last_drop_report = 0.0
        self._max_queue_bytes = max_queue_bytes
        self._queued_bytes = 0
        self._in_flight: list[ConsoleFrame | ConsoleCommandRecord] = []

    @property
    def dropped(self) -> int:
        """Frames discarded because the queue was full."""
        return self._dropped

    @property
    def queued_bytes(self) -> int:
        """Resident size of the backlog."""
        return self._queued_bytes

    async def start(self) -> None:
        """Starts the flusher."""
        if self._task is None:
            self._task = asyncio.create_task(self._flush_loop())

    async def stop(self) -> None:
        """Stops the flusher, writing whatever is still queued."""
        task, self._task = self._task, None
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        await self._drain_once()

    def submit(self, frame: ConsoleFrame | ConsoleCommandRecord) -> None:
        """Enqueues a frame. Never blocks, never raises."""
        size = _frame_bytes(frame)
        if self._queued_bytes + size > self._max_queue_bytes:
            self._drop(size)
            return
        try:
            self._queue.put_nowait(frame)
        except asyncio.QueueFull:
            self._drop(size)
            return
        self._queued_bytes += size

    def _drop(self, size: int) -> None:
        """Counts a dropped frame, logging at most once per 10s."""
        self._dropped += 1
        now = time.monotonic()
        if now - self._last_drop_report > 10.0:
            self._last_drop_report = now
            logger.warning(
                "console capture: backlog full, dropped %d frames, %d bytes queued",
                self._dropped,
                self._queued_bytes,
            )

    def tap(self, session_id: uuid.UUID, node_id: str) -> ConsoleTap:
        """Creates a tap for one console socket."""
        return ConsoleTap(self, session_id, node_id)

    async def _flush_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(self._flush_interval)
                await self._drain_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("console capture: flush failed")

    async def _drain_once(self) -> None:
        """Writes every queued frame, resuming a batch a cancellation interrupted."""
        if self._db_factory is None:
            return
        while True:
            batch = self._in_flight
            self._in_flight = []
            while len(batch) < self._batch_size:
                try:
                    item = self._queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                self._queued_bytes -= _frame_bytes(item)
                batch.append(item)
            if not batch:
                return
            # Kept until the write returns.
            self._in_flight = batch
            try:
                await self._write(batch)
            except Exception:
                logger.exception("console capture: dropping a batch of %d frames", len(batch))
            self._in_flight = []
            await asyncio.sleep(0)

    async def _write(self, batch: list[ConsoleFrame | ConsoleCommandRecord]) -> None:
        from src.db.models import ConsoleChunk, ConsoleCommand

        records = [item for item in batch if isinstance(item, ConsoleCommandRecord)]
        chunk_rows: list = []
        command_rows: list = []
        for item in batch:
            if isinstance(item, ConsoleFrame):
                chunk_rows.append(
                    ConsoleChunk(
                        session_id=item.session_id,
                        node_id=item.node_id,
                        connection_id=item.connection_id,
                        seq=item.seq,
                        direction=item.direction,
                        payload=item.payload,
                        truncated=item.truncated,
                        redacted=item.redacted,
                        ts=item.ts,
                    )
                )
            else:
                command_rows.append(
                    ConsoleCommand(
                        session_id=item.session_id,
                        node_id=item.node_id,
                        connection_id=item.connection_id,
                        seq=item.seq,
                        prompt=item.prompt,
                        command=item.command,
                        response=item.response,
                        ts=item.ts,
                        duration_ms=item.duration_ms,
                    )
                )
        # Isolate chunk and command commits.
        if chunk_rows:
            try:
                async with self._db_factory() as db:
                    db.add_all(chunk_rows)
                    await db.commit()
                    # Replay can no longer repeat them.
                    self._in_flight = records
            except Exception:
                logger.exception("console capture: dropping %d chunk rows", len(chunk_rows))
        if command_rows:
            try:
                async with self._db_factory() as db:
                    db.add_all(command_rows)
                    await db.commit()
                    self._in_flight = []
            except Exception:
                logger.exception("console capture: dropping %d command rows", len(command_rows))


class ConsoleTap:
    """Per-socket capture state; sequence numbers never interleave."""

    def __init__(self, capture: ConsoleCapture, session_id: uuid.UUID, node_id: str) -> None:
        self._capture = capture
        self._session_id = session_id
        self._node_id = node_id[:MAX_NODE_ID_CHARS]
        self.connection_id = uuid.uuid4()
        self._seq = 0
        self._bytes = 0
        self._over_budget = False
        self._max_rows = MAX_CONNECTION_ROWS
        self._rows = 0
        self._tail = b""
        self._password_mode = False
        self._reconstructor = ConsoleReconstructor()
        self._pending_enters: deque[datetime] = deque(maxlen=_MAX_PENDING_ENTERS)
        self._last_enter_match = datetime.now(UTC)
        self._buffers = {"in": _DirectionBuffer(), "out": _DirectionBuffer()}

    def from_client(self, data: bytes) -> None:
        """Records bytes the learner typed, masked during password prompts."""
        self._ingest("in", data)
        # Count keypresses; CRLF collapsed first.
        now = datetime.now(UTC)
        collapsed = data.replace(CR + LF, LF)
        for _ in range(collapsed.count(CR) + collapsed.count(LF)):
            self._pending_enters.append(now)

    def from_node(self, data: bytes) -> None:
        """Records node output, detects password prompts, reconstructs commands."""
        self._ingest("out", data)
        self._emit(self._reconstructor.feed(data, datetime.now(UTC)))
        # Tracked even over budget.
        self._tail = (self._tail + data)[-_TAIL_BYTES:]
        if _PASSWORD_PROMPT_RE.search(self._tail):
            self._password_mode = True

    def close(self) -> None:
        """Closes the socket's state, flushing buffered bytes and open command."""
        for direction in ("in", "out"):
            buffer = self._buffers[direction]
            while buffer.data and not self._over_budget:
                size = min(len(buffer.data), MAX_CHUNK_BYTES)
                self._emit_buffer(direction, size, truncated=size < len(buffer.data))
        self._emit(self._reconstructor.flush())

    def _is_learner_command(self, command) -> bool:
        """True when the learner ran it, not a platform probe."""
        cutoff = command.ts - _LEARNER_ENTER_WINDOW
        # Keeps a paste's queue alive.
        while (
            self._pending_enters and max(self._pending_enters[0], self._last_enter_match) < cutoff
        ):
            self._pending_enters.popleft()
        if self._pending_enters and self._pending_enters[0] <= command.ts:
            self._pending_enters.popleft()
            self._last_enter_match = command.ts
            return True
        return False

    def _over_row_budget(self) -> bool:
        """Whether this connection has written its allowance."""
        if self._rows >= self._max_rows:
            if not self._over_budget:
                self._over_budget = True
                logger.warning(
                    "console capture: connection %s hit the row budget, capture off",
                    self.connection_id,
                )
            return True
        self._rows += 1
        return False

    def _emit(self, commands) -> None:
        """Queues learner commands, skipping platform probes; passwords never appear."""
        for command in commands:
            if not self._is_learner_command(command):
                continue
            if self._over_budget or self._over_row_budget():
                continue
            text, _ = redact_secrets(command.command.encode())
            response, _ = redact_secrets(command.response.encode())
            self._capture.submit(
                ConsoleCommandRecord(
                    session_id=self._session_id,
                    node_id=self._node_id,
                    connection_id=self.connection_id,
                    seq=command.seq,
                    prompt=(command.prompt or "")[:MAX_PROMPT_CHARS] or None,
                    command=text.decode("utf-8", errors="replace"),
                    response=response.decode("utf-8", errors="replace"),
                    ts=command.ts,
                    duration_ms=command.duration_ms,
                )
            )

    def _mask_password(self, data: bytes) -> tuple[bytes, bool]:
        """Replaces the secret with stars, keeping its length."""
        masked = bytearray()
        redacted = False
        start = 0
        while self._password_mode and start < len(data):
            breaks = [
                position
                for position in (data.find(CR, start), data.find(LF, start))
                if position != -1
            ]
            if not breaks:
                masked.extend(b"*" * (len(data) - start))
                return bytes(masked), True
            end = min(breaks)
            masked.extend(b"*" * (end - start))
            # An empty line keeps masking armed.
            if end > start:
                redacted = True
                self._password_mode = False
                self._tail = b""
            masked.append(data[end])
            start = end + 1
        masked.extend(data[start:])
        return bytes(masked), redacted

    def _ingest(self, direction: str, data: bytes) -> None:
        """Buffers raw bytes; a full line becomes a frame."""
        if self._over_budget or not data:
            return
        # Counts raw ingested bytes.
        self._bytes += len(data)
        if self._bytes > MAX_CONNECTION_BYTES:
            self._over_budget = True
            logger.warning(
                "console capture: connection %s hit the byte budget, capture off",
                self.connection_id,
            )
            return
        buffer = self._buffers[direction]
        if not buffer.data:
            buffer.ts = datetime.now(UTC)
        # Everything before the new bytes was searched already.
        searched = len(buffer.data)
        buffer.data.extend(data)
        while not self._over_budget:
            limit = min(len(buffer.data), MAX_CHUNK_BYTES)
            break_at = max(
                buffer.data.rfind(CR, searched, limit),
                buffer.data.rfind(LF, searched, limit),
            )
            if break_at >= 0:
                self._emit_buffer(direction, break_at + 1, truncated=False)
            elif len(buffer.data) >= MAX_CHUNK_BYTES:
                self._emit_buffer(direction, MAX_CHUNK_BYTES, truncated=True)
            else:
                return
            searched = 0

    def _emit_buffer(self, direction: str, size: int, truncated: bool) -> None:
        """Turns the head of one direction's buffer into a frame."""
        buffer = self._buffers[direction]
        payload = bytes(buffer.data[:size])
        ts = buffer.ts or datetime.now(UTC)
        del buffer.data[:size]
        buffer.ts = datetime.now(UTC) if buffer.data else None
        redacted = False
        if direction == "in" and self._password_mode:
            payload, redacted = self._mask_password(payload)
        payload, secret_found = redact_secrets(payload)
        if self._over_row_budget():
            return
        self._seq += 1
        self._capture.submit(
            ConsoleFrame(
                session_id=self._session_id,
                node_id=self._node_id,
                connection_id=self.connection_id,
                seq=self._seq,
                direction=direction,
                payload=payload,
                truncated=truncated,
                redacted=redacted or secret_found,
                ts=ts,
            )
        )
