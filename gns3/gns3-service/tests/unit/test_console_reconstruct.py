"""Unit tests for reconstructing commands from a console byte stream."""

from datetime import UTC, datetime, timedelta

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from src.console_reconstruct import ConsoleReconstructor, reconstruct

pytestmark = [pytest.mark.unit]

_T0 = datetime(2026, 9, 9, 12, 0, 0, tzinfo=UTC)


def _out(*payloads: bytes, step_ms: int = 100):
    """Builds `out` frames, one step apart."""
    return [
        ("out", payload, _T0 + timedelta(milliseconds=step_ms * i))
        for i, payload in enumerate(payloads)
    ]


class TestReconstructBasics:
    """A command is taken from the device echo, its output from what follows."""

    @autotest.name("reconstruct: one command and its response")
    def test_single_command(self):
        with autotest.step("Arrange: echo, output, next prompt"):
            frames = _out(b"R1#show ip route\r\n", b"O 10.0.0.0/8\r\n", b"R1#")

        with autotest.step("Act"):
            commands = reconstruct(frames)

        with autotest.step("Assert"):
            assert_equal(len(commands), 1, "count")
            assert_equal(commands[0].command, "show ip route", "command")
            assert_equal(commands[0].response, "O 10.0.0.0/8", "response")
            assert_equal(commands[0].prompt, "R1#", "prompt")

    @autotest.name("reconstruct: several commands in one stream")
    def test_multiple_commands(self):
        with autotest.step("Arrange"):
            frames = _out(
                b"R1#conf t\r\n",
                b"Enter configuration commands.\r\n",
                b"R1(config)#interface fa0/0\r\n",
                b"R1(config-if)#",
            )

        with autotest.step("Act"):
            commands = reconstruct(frames)

        with autotest.step("Assert: both commands, each with its own prompt"):
            assert_equal([c.command for c in commands], ["conf t", "interface fa0/0"], "commands")
            assert_equal([c.prompt for c in commands], ["R1#", "R1(config)#"], "prompts")

    @autotest.name("reconstruct: a bare prompt is not a command")
    def test_bare_prompt_ignored(self):
        with autotest.step("Arrange: the learner just pressed Enter twice"):
            frames = _out(b"R1#\r\n", b"R1#\r\n", b"R1#")

        with autotest.step("Act + Assert"):
            assert_equal(len(reconstruct(frames)), 0, "count")

    @autotest.name("reconstruct: duration is measured to the next prompt")
    def test_duration_measured(self):
        with autotest.step("Arrange: prompt arrives 300ms after the command"):
            frames = _out(b"R1#ping 10.0.0.1\r\n", b"!!!!!\r\n", b"R1#", step_ms=300)

        with autotest.step("Act"):
            commands = reconstruct(frames)

        with autotest.step("Assert"):
            assert_equal(commands[0].duration_ms, 600.0, "duration_ms")


class TestReconstructNoise:
    """Terminal control bytes must not leak into the stored text."""

    @autotest.name("reconstruct: ANSI escape sequences are stripped")
    def test_strips_ansi(self):
        with autotest.step("Arrange: coloured output"):
            frames = _out(
                b"R1#show version\r\n",
                b"\x1b[32mIOS Version 15.2\x1b[0m\r\n",
                b"R1#",
            )

        with autotest.step("Act"):
            commands = reconstruct(frames)

        with autotest.step("Assert"):
            assert_equal(commands[0].response, "IOS Version 15.2", "response")

    @autotest.name("reconstruct: backspaces in the echo are applied")
    def test_applies_backspace(self):
        with autotest.step("Arrange: the learner typed shy, erased y, typed ow"):
            frames = _out(b"R1#shy\x08 \x08ow ip route\r\n", b"R1#")

        with autotest.step("Act"):
            commands = reconstruct(frames)

        with autotest.step("Assert: the corrected command is what is stored"):
            assert_equal(commands[0].command, "show ip route", "command")

    @autotest.name("reconstruct: the pager marker is dropped from the response")
    def test_drops_pager_marker(self):
        with autotest.step("Arrange"):
            frames = _out(
                b"R1#show running-config\r\n",
                b"hostname R1\r\n",
                b" --More-- \r\n",
                b"interface fa0/0\r\n",
                b"R1#",
            )

        with autotest.step("Act"):
            commands = reconstruct(frames)

        with autotest.step("Assert"):
            assert_equal(commands[0].response, "hostname R1\n\ninterface fa0/0", "response")

    @autotest.name("reconstruct: a frame split mid-line is reassembled")
    def test_reassembles_split_frames(self):
        with autotest.step("Arrange: the command arrives one keystroke per frame"):
            frames = _out(b"R1#sh", b"ow ip ", b"route\r\n", b"O 10.0.0.0/8\r\n", b"R1#")

        with autotest.step("Act"):
            commands = reconstruct(frames)

        with autotest.step("Assert"):
            assert_equal(commands[0].command, "show ip route", "command")
            assert_equal(commands[0].response, "O 10.0.0.0/8", "response")


class TestReconstructStreaming:
    """Commands come out as soon as the next prompt appears, not at the end."""

    @autotest.name("ConsoleReconstructor: a command is emitted when the next prompt arrives")
    def test_emits_on_next_prompt(self):
        with autotest.step("Arrange"):
            reconstructor = ConsoleReconstructor()

        with autotest.step("Act: feed the command, then its output"):
            first = reconstructor.feed(b"R1#show clock\r\n", _T0)
            second = reconstructor.feed(b"12:00:00 UTC\r\n", _T0)

        with autotest.step("Assert: nothing is emitted until the prompt returns"):
            assert_equal(len(first), 0, "after the command")
            assert_equal(len(second), 0, "after the output")

        with autotest.step("Act: the prompt returns"):
            third = reconstructor.feed(b"R1#", _T0)

        with autotest.step("Assert"):
            assert_equal(len(third), 1, "after the prompt")
            assert_equal(third[0].command, "show clock", "command")

    @autotest.name("ConsoleReconstructor: flush closes the command still open")
    def test_flush_closes_open_command(self):
        with autotest.step("Arrange: a command whose prompt never came back"):
            reconstructor = ConsoleReconstructor()
            reconstructor.feed(b"R1#reload\r\n", _T0)
            reconstructor.feed(b"System going down\r\n", _T0)

        with autotest.step("Act: the socket goes away"):
            commands = reconstructor.flush()

        with autotest.step("Assert"):
            assert_equal(len(commands), 1, "count")
            assert_equal(commands[0].command, "reload", "command")
            assert_equal(commands[0].response, "System going down", "response")

    @autotest.name("ConsoleReconstructor: the typed direction is not read")
    def test_ignores_input_direction(self):
        with autotest.step("Arrange: only `in` frames, which carry keystrokes"):
            frames = [("in", b"show ip route\r", _T0)]

        with autotest.step("Act + Assert: nothing is reconstructed from them"):
            assert_equal(len(reconstruct(frames)), 0, "count")
