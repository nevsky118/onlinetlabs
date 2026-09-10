"""Capture of node console traffic that crosses the console WS proxy.

Two rules shape everything here:

1. Capture must never slow the console down. ConsoleTap.record only stamps a
   sequence number and drops the frame into a queue; a background task does the
   database work. When the queue is full the frame is dropped and counted, never
   awaited - a stalled database must not turn into lag while a learner types.
2. Capture must never break the console. Every failure path is swallowed and
   logged, and the proxy keeps relaying with capture disabled.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
import uuid
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.console_reconstruct import ConsoleReconstructor

logger = logging.getLogger(__name__)

# A single frame larger than this is stored truncated. Console frames are
# normally tiny; a huge one means a "show tech-support" style dump.
MAX_CHUNK_BYTES = 64 * 1024

# Once a connection has produced this much, capture stops for that socket. Keeps
# one runaway console from filling the table.
MAX_CONNECTION_BYTES = 8 * 1024 * 1024

# The tail of node output is matched against this to notice an open password
# prompt. "assword" rather than "password" so it matches either case, and
# [^\S\r\n] is "space or tab but not a newline".
_PASSWORD_PROMPT_RE = re.compile(rb"assword[^\S\r\n]*:[^\S\r\n]*\Z", re.IGNORECASE)

# How much of the node output tail is kept to match the prompt against.
_TAIL_BYTES = 64

# How long after a keypress the echo of that command may still arrive. A device
# echoes as you type, so the gap is milliseconds; the window is generous only so
# a loaded node cannot cost us a real command.
_LEARNER_ENTER_WINDOW = timedelta(seconds=2.0)

# Enough pending keypresses for any realistic burst of typing.
_MAX_PENDING_ENTERS = 32

# The bytes a keyboard sends for Enter.
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


class ConsoleCapture:
    """Queue plus a background flusher writing console frames in batches."""

    def __init__(
        self,
        db_factory,
        *,
        queue_size: int = 10_000,
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

    @property
    def dropped(self) -> int:
        """Frames discarded because the queue was full."""
        return self._dropped

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
        await self._drain_once(final=True)

    def submit(self, frame: ConsoleFrame | ConsoleCommandRecord) -> None:
        """Enqueues a frame. Never blocks, never raises."""
        try:
            self._queue.put_nowait(frame)
        except asyncio.QueueFull:
            self._dropped += 1
            now = time.monotonic()
            # One line per 10s: a saturated queue would otherwise flood the log
            # with exactly the message that is least useful when repeated.
            if now - self._last_drop_report > 10.0:
                self._last_drop_report = now
                logger.warning("console capture: queue full, dropped %d frames", self._dropped)

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

    async def _drain_once(self, final: bool = False) -> None:
        """Writes up to one batch, or everything still queued when final."""
        if self._db_factory is None:
            return
        while True:
            batch: list[ConsoleFrame | ConsoleCommandRecord] = []
            while len(batch) < self._batch_size:
                try:
                    batch.append(self._queue.get_nowait())
                except asyncio.QueueEmpty:
                    break
            if not batch:
                return
            try:
                await self._write(batch)
            except Exception:
                logger.exception("console capture: dropping a batch of %d frames", len(batch))
            if not final:
                return

    async def _write(self, batch: list[ConsoleFrame | ConsoleCommandRecord]) -> None:
        from src.db.models import ConsoleChunk, ConsoleCommand

        rows: list = []
        for item in batch:
            if isinstance(item, ConsoleFrame):
                rows.append(
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
                rows.append(
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
        async with self._db_factory() as db:
            db.add_all(rows)
            await db.commit()


class ConsoleTap:
    """Per-socket capture state: ordering, byte budget, password masking.

    Not thread-safe and does not need to be: both relay directions of one socket
    run as tasks on the same event loop, and neither awaits inside _record, so
    the sequence number cannot interleave.
    """

    def __init__(self, capture: ConsoleCapture, session_id: uuid.UUID, node_id: str) -> None:
        self._capture = capture
        self._session_id = session_id
        self._node_id = node_id
        self.connection_id = uuid.uuid4()
        self._seq = 0
        self._bytes = 0
        self._over_budget = False
        self._tail = b""
        self._password_mode = False
        self._reconstructor = ConsoleReconstructor()
        self._pending_enters: deque[datetime] = deque(maxlen=_MAX_PENDING_ENTERS)

    def from_client(self, data: bytes) -> None:
        """Records bytes the learner typed, masked while a password prompt is open."""
        redacted = False
        if self._password_mode:
            data, redacted = self._mask_password(data)
        self._record("in", data, redacted)
        # Every command a learner runs ends with them sending a carriage return.
        # Nothing else on this socket produces one, which is what later tells a
        # learner's command apart from a probe run by the platform.
        if CR in data or LF in data:
            self._pending_enters.append(datetime.now(UTC))

    def from_node(self, data: bytes) -> None:
        """Records bytes the node sent, notices a password prompt, reconstructs commands."""
        self._record("out", data, False)
        self._emit(self._reconstructor.feed(data, datetime.now(UTC)))
        # Tracked even when over budget: missing the prompt would unmask the next
        # password typed on this socket.
        self._tail = (self._tail + data)[-_TAIL_BYTES:]
        if _PASSWORD_PROMPT_RE.search(self._tail):
            self._password_mode = True

    def close(self) -> None:
        """Closes the socket's state, emitting the command still in flight."""
        self._emit(self._reconstructor.flush())

    def _is_learner_command(self, command) -> bool:
        """Whether a learner ran this command, rather than the platform probing.

        A node console is shared: gns3-server relays its output to everyone
        attached, and the platform's own spec checks reach the same node over
        telnet (see the validation checks that write "show ip" every poll). Their
        echo arrives on this socket looking exactly like a learner's command, and
        recording it would fill the behavioural data with the platform's own
        regular heartbeat.

        The learner's keypresses are the thing a probe cannot fake: they crossed
        this WebSocket. So a command counts as the learner's only if one of their
        carriage returns is still unclaimed and arrived just before the echo.
        Matching on the keypress rather than on the typed text keeps commands
        recalled from history or finished with Tab, where the learner sends
        almost no characters of the command itself.
        """
        cutoff = command.ts - _LEARNER_ENTER_WINDOW
        while self._pending_enters and self._pending_enters[0] < cutoff:
            self._pending_enters.popleft()
        if self._pending_enters and self._pending_enters[0] <= command.ts:
            self._pending_enters.popleft()
            return True
        return False

    def _emit(self, commands) -> None:
        """Queues the commands a learner ran, dropping the platform's probes.

        A password is never among them: it is typed at a prompt the device does
        not echo, and the reconstructor reads the node's output, not keystrokes.
        """
        for command in commands:
            if not self._is_learner_command(command):
                continue
            self._capture.submit(
                ConsoleCommandRecord(
                    session_id=self._session_id,
                    node_id=self._node_id,
                    connection_id=self.connection_id,
                    seq=command.seq,
                    prompt=command.prompt,
                    command=command.command,
                    response=command.response,
                    ts=command.ts,
                    duration_ms=command.duration_ms,
                )
            )

    def _mask_password(self, data: bytes) -> tuple[bytes, bool]:
        """Replaces the secret with stars, keeping length so keystroke counts survive.

        The device never echoes a password, so "out" is clean - but "in" carries
        it in the clear, which is why this runs before the frame is queued rather
        than on the way back out of the database.
        """
        breaks = [i for i in (data.find(b"\r"), data.find(b"\n")) if i != -1]
        if not breaks:
            return b"*" * len(data), True
        end = min(breaks)
        self._password_mode = False
        self._tail = b""
        return b"*" * end + data[end:], end > 0

    def _record(self, direction: str, data: bytes, redacted: bool) -> None:
        if self._over_budget or not data:
            return
        self._bytes += len(data)
        if self._bytes > MAX_CONNECTION_BYTES:
            self._over_budget = True
            logger.warning(
                "console capture: connection %s hit the byte budget, capture off",
                self.connection_id,
            )
            return
        truncated = len(data) > MAX_CHUNK_BYTES
        self._seq += 1
        self._capture.submit(
            ConsoleFrame(
                session_id=self._session_id,
                node_id=self._node_id,
                connection_id=self.connection_id,
                seq=self._seq,
                direction=direction,
                payload=data[:MAX_CHUNK_BYTES] if truncated else data,
                truncated=truncated,
                redacted=redacted,
                ts=datetime.now(UTC),
            )
        )
