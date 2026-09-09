"""Turns a raw console byte stream back into commands and their output.

Reconstruction reads the node's own output rather than the learner's keystrokes.
That sounds backwards, but the output is the better source: the device echoes
every character it accepted, so tab-completion arrives already expanded, a recalled
history entry arrives as the command it expanded to, and backspaces have already
been applied. The typed stream is kept for timing and keystroke counts, not for
the text of the command.

Streaming on purpose. Buffering a whole session and parsing it at the end would
hold megabytes per console; here only the current response is in memory, and a
finished command is handed over as soon as the next prompt appears.

Known limits, all of which show up as an odd row rather than lost data:

* A device can print unprompted (a Cisco `%LINK-3-UPDOWN` log lands mid-typing),
  so a response may carry lines the command did not cause.
* Paged output (`--More--`) is driven by spacebar presses; the marker is dropped
  but the pauses stay inside the measured duration.
* A response line that happens to look like a prompt splits a command in two.
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

# A prompt ends in # > or $, optionally preceded by a Cisco mode like (config-if).
# The command, when present, follows on the same line because the device echoes
# it - and on IOS it follows the prompt with no space at all ("R1#show ip route"),
# so the separator has to be optional rather than required.
_PROMPT_RE = re.compile(r"^(?P<prompt>[\w.@:~/\-\[\]]+(?:\([^)]*\))?\s?[#>$])\s?(?P<command>.*)$")

# One response is capped so a `show tech-support` cannot grow without bound.
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
        # A prompt arrives without a trailing newline - the device is waiting for
        # input. That is exactly what closes the previous command, so the tail is
        # inspected without being consumed.
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
        # A prompt line ends the previous command whether or not a new one
        # follows it: a bare prompt is the learner pressing Enter.
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
