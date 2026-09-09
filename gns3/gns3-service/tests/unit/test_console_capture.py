"""Unit tests for console capture and the console WS path parser."""

import uuid

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from src.console_capture import MAX_CONNECTION_BYTES, ConsoleCapture
from src.routers.console_ws import parse_console_path

pytestmark = [pytest.mark.unit]


def _capture() -> ConsoleCapture:
    """Capture with no database: frames stay in the queue for inspection."""
    return ConsoleCapture(db_factory=None)


def _drain(capture: ConsoleCapture) -> list:
    frames = []
    while not capture._queue.empty():
        frames.append(capture._queue.get_nowait())
    return frames


class TestParseConsolePath:
    """The parser must accept both GNS3 console URL shapes and reject the rest."""

    @autotest.name("parse_console_path: controller-level URL yields project and node")
    def test_controller_level_path(self):
        with autotest.step("Act"):
            parsed = parse_console_path("/v3/projects/proj-1/nodes/node-1/console/ws")

        with autotest.step("Assert"):
            assert_equal(parsed, ("proj-1", "node-1"), "parsed")

    @autotest.name("parse_console_path: compute-level URL yields project and node")
    def test_compute_level_path(self):
        with autotest.step("Act"):
            parsed = parse_console_path("/v3/compute/projects/proj-2/nodes/node-2/console/ws")

        with autotest.step("Assert"):
            assert_equal(parsed, ("proj-2", "node-2"), "parsed")

    @autotest.name("parse_console_path: a non-console path is rejected")
    def test_rejects_non_console_path(self):
        with autotest.step("Act + Assert"):
            assert_equal(parse_console_path("/v3/projects/proj-1/nodes"), None, "parsed")
            assert_equal(parse_console_path("/v3/projects/proj-1/notifications/ws"), None, "parsed")


class TestConsoleTapOrdering:
    """Both directions share one sequence, so a replay can interleave them."""

    @autotest.name("ConsoleTap: both directions share one monotonic sequence")
    def test_shared_sequence(self):
        with autotest.step("Arrange"):
            capture = _capture()
            tap = capture.tap(uuid.uuid4(), "node-1")

        with autotest.step("Act: interleave typed bytes and node output"):
            tap.from_client(b"sh")
            tap.from_node(b"sh")
            tap.from_client(b"\r")
            tap.from_node(b"\r\nR1#")

        with autotest.step("Assert: sequence counts up across directions"):
            frames = _drain(capture)
            assert_equal([f.seq for f in frames], [1, 2, 3, 4], "seq")
            assert_equal([f.direction for f in frames], ["in", "out", "in", "out"], "direction")

    @autotest.name("ConsoleTap: an empty frame is not recorded")
    def test_empty_frame_skipped(self):
        with autotest.step("Arrange"):
            capture = _capture()
            tap = capture.tap(uuid.uuid4(), "node-1")

        with autotest.step("Act"):
            tap.from_client(b"")

        with autotest.step("Assert"):
            assert_equal(len(_drain(capture)), 0, "frames")

    @autotest.name("ConsoleTap: capture stops once the connection byte budget is spent")
    def test_byte_budget_stops_capture(self):
        with autotest.step("Arrange"):
            capture = _capture()
            tap = capture.tap(uuid.uuid4(), "node-1")

        with autotest.step("Act: exceed the budget, then send more"):
            tap.from_node(b"x" * (MAX_CONNECTION_BYTES + 1))
            _drain(capture)
            tap.from_node(b"still talking")

        with autotest.step("Assert: nothing is recorded after the budget is spent"):
            assert_equal(len(_drain(capture)), 0, "frames")


class TestPasswordRedaction:
    """A password reaches us only in the typed direction, so it is masked there."""

    @autotest.name("ConsoleTap: input after a password prompt is masked")
    def test_masks_password_after_prompt(self):
        with autotest.step("Arrange: the node asks for a password"):
            capture = _capture()
            tap = capture.tap(uuid.uuid4(), "node-1")
            tap.from_node(b"\r\nPassword: ")
            _drain(capture)

        with autotest.step("Act: the learner types the secret"):
            tap.from_client(b"s3cret")

        with autotest.step("Assert: stars are stored, length preserved"):
            frames = _drain(capture)
            assert_equal(frames[0].payload, b"******", "payload")
            assert_equal(frames[0].redacted, True, "redacted")

    @autotest.name("ConsoleTap: masking stops at the newline that ends the password")
    def test_masking_stops_at_newline(self):
        with autotest.step("Arrange"):
            capture = _capture()
            tap = capture.tap(uuid.uuid4(), "node-1")
            tap.from_node(b"Password: ")
            _drain(capture)

        with autotest.step("Act: secret and newline arrive together, then a command"):
            tap.from_client(b"s3cret\r")
            tap.from_client(b"show ip route")

        with autotest.step("Assert: only the secret is masked"):
            frames = _drain(capture)
            assert_equal(frames[0].payload, b"******\r", "masked payload")
            assert_equal(frames[1].payload, b"show ip route", "later command")
            assert_equal(frames[1].redacted, False, "later command not redacted")

    @autotest.name("ConsoleTap: ordinary input is stored verbatim")
    def test_plain_input_not_masked(self):
        with autotest.step("Arrange"):
            capture = _capture()
            tap = capture.tap(uuid.uuid4(), "node-1")

        with autotest.step("Act"):
            tap.from_client(b"conf t\r")

        with autotest.step("Assert"):
            frames = _drain(capture)
            assert_equal(frames[0].payload, b"conf t\r", "payload")
            assert_equal(frames[0].redacted, False, "redacted")


class TestQueueBackpressure:
    """A full queue drops frames rather than making the learner wait."""

    @autotest.name("ConsoleCapture: submitting to a full queue drops and counts")
    def test_drops_when_full(self):
        with autotest.step("Arrange: a queue of one"):
            capture = ConsoleCapture(db_factory=None, queue_size=1)
            tap = capture.tap(uuid.uuid4(), "node-1")

        with autotest.step("Act: send two frames"):
            tap.from_client(b"a")
            tap.from_client(b"b")

        with autotest.step("Assert: one queued, one counted as dropped"):
            assert_equal(capture._queue.qsize(), 1, "queued")
            assert_equal(capture.dropped, 1, "dropped")
