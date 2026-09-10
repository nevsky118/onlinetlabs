"""Turns a raw console byte stream back into commands and their output.

Reads the node's echo, not the keystrokes: the echo arrives with tab-completion
expanded, history recalled and backspaces applied. Streaming, so only the current
response is ever in memory.

Known limits, which show up as an odd row rather than lost data: unprompted device
logs land inside a response, `--More--` pauses inflate the duration, and a response
line that looks like a prompt splits a command in two.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

# CSI sequences (colours, cursor moves), OSC title strings, and charset selects.
_ANSI_RE = re.compile(rb"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[()][B0]")

# Pager marker, with or without the backspaces a device uses to erase it.
_MORE_RE = re.compile(rb"--\s*More\s*--")

# Control bytes that carry no text once backspaces have been applied.
_CONTROL_RE = re.compile(rb"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Prompt ends in # > or $, optionally with a Cisco mode like (config-if). On IOS
# the command follows with no space ("R1#show ip route"), so the gap is optional.
_PROMPT_RE = re.compile(r"^(?P<prompt>[\w.@:~/\-\[\]]+(?:\([^)]*\))?\s?[#>$])\s?(?P<command>.*)$")

# Caps a runaway `show tech-support`.
MAX_RESPONSE_CHARS = 256 * 1024


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
        self._buf = b""
        self._seq = 0
        self._open: ReconstructedCommand | None = None
        self._response: list[str] = []
        self._response_chars = 0
        self._last_ts: datetime | None = None

    def feed(self, data: bytes, ts: datetime) -> list[ReconstructedCommand]:
        """Consumes node output, returning any commands completed by it."""
        self._buf += data
        self._last_ts = ts
        finished: list[ReconstructedCommand] = []
        while True:
            match = re.search(rb"\r\n|\n|\r", self._buf)
            if match is None:
                break
            line, self._buf = self._buf[: match.start()], self._buf[match.end() :]
            self._consume(_clean(line), ts, finished)
        # A prompt with no trailing newline means the device is waiting: that
        # closes the previous command, so peek at the tail without consuming it.
        tail = _clean(self._buf)
        if tail and _PROMPT_RE.match(tail):
            self._close(ts, finished)
        return finished

    def flush(self) -> list[ReconstructedCommand]:
        """Closes whatever is still open, for when the socket goes away."""
        finished: list[ReconstructedCommand] = []
        if self._buf:
            self._consume(_clean(self._buf), self._last_ts, finished)
            self._buf = b""
        self._close(self._last_ts, finished)
        return finished

    def _consume(self, line: str, ts: datetime | None, finished: list) -> None:
        match = _PROMPT_RE.match(line) if line else None
        if match is None:
            if self._open is not None and self._response_chars < MAX_RESPONSE_CHARS:
                self._response.append(line)
                self._response_chars += len(line) + 1
            return
        # A prompt ends the previous command even with nothing after it.
        self._close(ts, finished)
        command = (match.group("command") or "").strip()
        if command and ts is not None:
            self._seq += 1
            self._open = ReconstructedCommand(
                seq=self._seq,
                prompt=match.group("prompt"),
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
    """Runs the reconstructor over stored frames. Only the `out` direction is read."""
    reconstructor = ConsoleReconstructor()
    commands: list[ReconstructedCommand] = []
    for direction, payload, ts in frames:
        if direction == "out":
            commands.extend(reconstructor.feed(payload, ts))
    commands.extend(reconstructor.flush())
    return commands
