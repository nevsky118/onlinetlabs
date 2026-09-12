"""Reconstructs commands and their output from a console byte stream."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

# ANSI/OSC escape sequences.
_ANSI_RE = re.compile(rb"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[()][B0]")

# Pager prompt marker.
_MORE_RE = re.compile(rb"--\s*More\s*--")

# Non-text control bytes.
_CONTROL_RE = re.compile(rb"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Matches a CLI prompt line.
_PROMPT_RE = re.compile(r"^(?P<prompt>[\w.@:~/\-\[\]]+(?:\([^)]*\))?\s?[#>$])\s?(?P<command>.*)$")

# Ends one console line.
_LINE_BREAK_RE = re.compile(rb"\r\n|\n|\r")

# Caps a runaway `show tech-support`.
MAX_RESPONSE_CHARS = 256 * 1024

# Bounds the unterminated tail.
MAX_BUFFER_BYTES = 8 * 1024

# Longest possible prompt tail.
MAX_PROMPT_TAIL_BYTES = 512


@dataclass(slots=True)
class ReconstructedCommand:
    """One command a learner ran, with what the node answered."""

    seq: int
    prompt: str
    command: str
    response: str
    ts: datetime
    duration_ms: float | None


def _clean(line: bytes) -> str:
    """Strips escape sequences, applies backspaces, drops the pager marker."""
    line = _ANSI_RE.sub(b"", line)
    line = _MORE_RE.sub(b"", line)
    out = bytearray()
    for byte in line:
        if byte in (0x08, 0x7F):
            if out:
                out.pop()
            continue
        out.append(byte)
    return _CONTROL_RE.sub(b"", bytes(out)).decode("utf-8", errors="replace").rstrip()


class ConsoleReconstructor:
    """Incremental parser: feed node output, get finished commands back."""

    def __init__(self) -> None:
        self._buf = bytearray()
        self._seq = 0
        self._open: ReconstructedCommand | None = None
        self._response: list[str] = []
        self._response_chars = 0
        self._last_ts: datetime | None = None

    def feed(self, data: bytes, ts: datetime) -> list[ReconstructedCommand]:
        """Consumes node output, returning any commands completed by it."""
        # Everything before the new bytes was searched already.
        searched = len(self._buf)
        self._buf.extend(data)
        self._last_ts = ts
        finished: list[ReconstructedCommand] = []
        line_start = 0
        while True:
            match = _LINE_BREAK_RE.search(self._buf, searched)
            if match is None:
                break
            self._consume(_clean(self._buf[line_start : match.start()]), ts, finished)
            line_start = searched = match.end()
        if line_start:
            del self._buf[:line_start]
        if len(self._buf) > MAX_BUFFER_BYTES:
            del self._buf[: len(self._buf) - MAX_BUFFER_BYTES // 2]
        # Trailing prompt implies command closed.
        if len(self._buf) <= MAX_PROMPT_TAIL_BYTES:
            tail = _clean(self._buf)
            if tail and _PROMPT_RE.match(tail):
                self._close(ts, finished)
        return finished

    def flush(self) -> list[ReconstructedCommand]:
        """Closes any command still open."""
        finished: list[ReconstructedCommand] = []
        if self._buf:
            self._consume(_clean(self._buf), self._last_ts, finished)
            self._buf.clear()
        self._close(self._last_ts, finished)
        return finished

    def _consume(self, line: str, ts: datetime | None, finished: list) -> None:
        match = _PROMPT_RE.match(line) if line else None
        if match is None:
            if self._open is not None and self._response_chars < MAX_RESPONSE_CHARS:
                self._response.append(line)
                self._response_chars += len(line) + 1
            return
        # Prompt always ends prior command.
        self._close(ts, finished)
        prompt = match.group("prompt")
        command = (match.group("command") or "").strip()
        # Drop the repeated tail prompt.
        while command.startswith(prompt):
            command = command[len(prompt) :].strip()
        if command and ts is not None:
            self._seq += 1
            self._open = ReconstructedCommand(
                seq=self._seq,
                prompt=prompt,
                command=command,
                response="",
                ts=ts,
                duration_ms=None,
            )

    def _close(self, ts: datetime | None, finished: list) -> None:
        if self._open is None:
            return
        self._open.response = "\n".join(self._response).strip("\n")
        if ts is not None:
            self._open.duration_ms = (ts - self._open.ts).total_seconds() * 1000
        finished.append(self._open)
        self._open = None
        self._response = []
        self._response_chars = 0


def reconstruct(frames: Iterable[tuple[str, bytes, datetime]]) -> list[ReconstructedCommand]:
    """Reconstructs commands from stored `out` frames."""
    reconstructor = ConsoleReconstructor()
    commands: list[ReconstructedCommand] = []
    for direction, payload, ts in frames:
        if direction == "out":
            commands.extend(reconstructor.feed(payload, ts))
    commands.extend(reconstructor.flush())
    return commands
