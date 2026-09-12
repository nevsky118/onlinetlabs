"""Unit tests for reconstructing commands from a console byte stream."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_less_equal

from src.console_reconstruct import (
    MAX_BUFFER_BYTES,
    MAX_PROMPT_TAIL_BYTES,
    ConsoleReconstructor,
    reconstruct,
)
from tests.settings.data.console_data import ConsoleCleanWorkData, ConsoleFrameSequenceData

pytestmark = [pytest.mark.unit]


class TestReconstructBasics:
    """Takes command from echo, output from what follows."""

    @autotest.num("3543")
    @autotest.external_id("2c02a377-1815-4dfe-8a49-ba1b67182259")
    @autotest.name("reconstruct: one command and its response")
    def test_2c02a377_single_command(self):
        with autotest.step("Arrange: echo, output, next prompt"):
            frames = ConsoleFrameSequenceData.out(
                b"R1#show ip route\r\n", b"O 10.0.0.0/8\r\n", b"R1#"
            )

        with autotest.step("Act"):
            commands = reconstruct(frames)

        with autotest.step("Assert"):
            assert_equal(len(commands), 1, "count")
            assert_equal(commands[0].command, "show ip route", "command")
            assert_equal(commands[0].response, "O 10.0.0.0/8", "response")
            assert_equal(commands[0].prompt, "R1#", "prompt")

    @autotest.num("3544")
    @autotest.external_id("6fd50041-242a-4410-9676-04cc90da759f")
    @autotest.name("reconstruct: several commands in one stream")
    def test_6fd50041_multiple_commands(self):
        with autotest.step("Arrange"):
            frames = ConsoleFrameSequenceData.out(
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

    @autotest.num("3545")
    @autotest.external_id("147b37f1-1677-4a3a-b3e9-7a55fcdc7460")
    @autotest.name("reconstruct: a bare prompt is not a command")
    def test_147b37f1_bare_prompt_ignored(self):
        with autotest.step("Arrange: the learner just pressed Enter twice"):
            frames = ConsoleFrameSequenceData.out(b"R1#\r\n", b"R1#\r\n", b"R1#")

        with autotest.step("Act + Assert"):
            assert_equal(len(reconstruct(frames)), 0, "count")

    @autotest.num("3546")
    @autotest.external_id("79e6d72c-d3a7-4835-997c-dab8c13a6dd5")
    @autotest.name("reconstruct: duration is measured to the next prompt")
    def test_79e6d72c_duration_measured(self):
        with autotest.step("Arrange: prompt arrives 300ms after the command"):
            frames = ConsoleFrameSequenceData.out(
                b"R1#ping 10.0.0.1\r\n", b"!!!!!\r\n", b"R1#", step_ms=300
            )

        with autotest.step("Act"):
            commands = reconstruct(frames)

        with autotest.step("Assert"):
            assert_equal(commands[0].duration_ms, 600.0, "duration_ms")


class TestReconstructNoise:
    """Strips terminal control bytes from stored text."""

    @autotest.num("3547")
    @autotest.external_id("920ea17b-c194-48f6-b99b-9c111c645dbc")
    @autotest.name("reconstruct: ANSI escape sequences are stripped")
    def test_920ea17b_strips_ansi(self):
        with autotest.step("Arrange: coloured output"):
            frames = ConsoleFrameSequenceData.out(
                b"R1#show version\r\n",
                b"\x1b[32mIOS Version 15.2\x1b[0m\r\n",
                b"R1#",
            )

        with autotest.step("Act"):
            commands = reconstruct(frames)

        with autotest.step("Assert"):
            assert_equal(commands[0].response, "IOS Version 15.2", "response")

    @autotest.num("3548")
    @autotest.external_id("60b77928-c0f6-4bd9-8aa0-0f77f68339be")
    @autotest.name("reconstruct: backspaces in the echo are applied")
    def test_60b77928_applies_backspace(self):
        with autotest.step("Arrange: the learner typed shy, erased y, typed ow"):
            frames = ConsoleFrameSequenceData.out(b"R1#shy\x08 \x08ow ip route\r\n", b"R1#")

        with autotest.step("Act"):
            commands = reconstruct(frames)

        with autotest.step("Assert: the corrected command is what is stored"):
            assert_equal(commands[0].command, "show ip route", "command")

    @autotest.num("3549")
    @autotest.external_id("b678e2da-adc3-4923-8b7a-cd236a8c8abb")
    @autotest.name("reconstruct: the pager marker is dropped from the response")
    def test_b678e2da_drops_pager_marker(self):
        with autotest.step("Arrange"):
            frames = ConsoleFrameSequenceData.out(
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

    @autotest.num("3550")
    @autotest.external_id("a9c00fd8-ab03-4b15-a7a6-88e06113dfcd")
    @autotest.name("reconstruct: a frame split mid-line is reassembled")
    def test_a9c00fd8_reassembles_split_frames(self):
        with autotest.step("Arrange: the command arrives one keystroke per frame"):
            frames = ConsoleFrameSequenceData.out(
                b"R1#sh", b"ow ip ", b"route\r\n", b"O 10.0.0.0/8\r\n", b"R1#"
            )

        with autotest.step("Act"):
            commands = reconstruct(frames)

        with autotest.step("Assert"):
            assert_equal(commands[0].command, "show ip route", "command")
            assert_equal(commands[0].response, "O 10.0.0.0/8", "response")


class TestReconstructStreaming:
    """Emits commands as soon as the next prompt appears."""

    @autotest.num("3551")
    @autotest.external_id("fe4be21a-9b96-4bb2-ae91-a53b077978d1")
    @autotest.name("ConsoleReconstructor: a command is emitted when the next prompt arrives")
    def test_fe4be21a_emits_on_next_prompt(self):
        with autotest.step("Arrange"):
            reconstructor = ConsoleReconstructor()

        with autotest.step("Act: feed the command, then its output"):
            first = reconstructor.feed(b"R1#show clock\r\n", ConsoleFrameSequenceData.T0)
            second = reconstructor.feed(b"12:00:00 UTC\r\n", ConsoleFrameSequenceData.T0)

        with autotest.step("Assert: nothing is emitted until the prompt returns"):
            assert_equal(len(first), 0, "after the command")
            assert_equal(len(second), 0, "after the output")

        with autotest.step("Act: the prompt returns"):
            third = reconstructor.feed(b"R1#", ConsoleFrameSequenceData.T0)

        with autotest.step("Assert"):
            assert_equal(len(third), 1, "after the prompt")
            assert_equal(third[0].command, "show clock", "command")

    @autotest.num("3552")
    @autotest.external_id("76844513-e1f9-4a5f-b736-db9cc2674006")
    @autotest.name("ConsoleReconstructor: flush closes the command still open")
    def test_76844513_flush_closes_open_command(self):
        with autotest.step("Arrange: a command whose prompt never came back"):
            reconstructor = ConsoleReconstructor()
            reconstructor.feed(b"R1#reload\r\n", ConsoleFrameSequenceData.T0)
            reconstructor.feed(b"System going down\r\n", ConsoleFrameSequenceData.T0)

        with autotest.step("Act: the socket goes away"):
            commands = reconstructor.flush()

        with autotest.step("Assert"):
            assert_equal(len(commands), 1, "count")
            assert_equal(commands[0].command, "reload", "command")
            assert_equal(commands[0].response, "System going down", "response")

    @autotest.num("3553")
    @autotest.external_id("6407f53e-a0e0-4024-9d38-0fdc93708fbe")
    @autotest.name("ConsoleReconstructor: the typed direction is not read")
    def test_6407f53e_ignores_input_direction(self):
        with autotest.step("Arrange: only `in` frames, which carry keystrokes"):
            frames = [("in", b"show ip route\r", ConsoleFrameSequenceData.T0)]

        with autotest.step("Act + Assert: nothing is reconstructed from them"):
            assert_equal(len(reconstruct(frames)), 0, "count")


class TestReconstructUnderLoad:
    """Unbroken output does not stall the event loop."""

    @autotest.num("3571")
    @autotest.external_id("97c13962-3af2-4e2f-a353-e3647548acd5")
    @autotest.name("ConsoleReconstructor: an unterminated burst leaves the buffer bounded")
    def test_97c13962_unterminated_burst_leaves_the_buffer_bounded(self):
        with autotest.step("Arrange"):
            reconstructor = ConsoleReconstructor()

        with autotest.step("Act: 64 KiB of output carrying no line break"):
            for _ in range(64):
                reconstructor.feed(b"x" * 1024, ConsoleFrameSequenceData.T0)

        with autotest.step("Assert: the buffer kept only its bound"):
            assert_less_equal(len(reconstructor._buf), MAX_BUFFER_BYTES, "buffered bytes")

    @autotest.num("3572")
    @autotest.external_id("7b7f2e60-017d-4d7d-a21e-52b66708ba34")
    @autotest.name("ConsoleReconstructor: cleaning cost stops growing with the burst")
    def test_7b7f2e60_cleaning_cost_stops_growing_with_the_burst(self, monkeypatch):
        with autotest.step("Arrange: count the bytes handed to the per-byte cleaner"):
            work = ConsoleCleanWorkData(monkeypatch)
            reconstructor = ConsoleReconstructor()

        with autotest.step("Act: 8000 one-byte feeds, as an interactive console delivers"):
            for _ in range(8000):
                reconstructor.feed(b"x", ConsoleFrameSequenceData.T0)

        with autotest.step("Assert: cleaning stops once the tail cannot be a prompt"):
            assert_less_equal(
                work.total, MAX_PROMPT_TAIL_BYTES * MAX_PROMPT_TAIL_BYTES, "cleaned bytes"
            )


class TestReconstructRepeatedPrompt:
    """A re-sent prompt is not folded into the next command."""

    @autotest.num("3575")
    @autotest.external_id("e2a217ff-afb9-4be3-8151-97e52df04966")
    @autotest.name("ConsoleReconstructor: a re-sent prompt is not doubled into the command")
    def test_e2a217ff_resent_prompt_is_not_doubled_into_the_command(self):
        with autotest.step("Arrange: the node leaves a trailing prompt in the buffer"):
            reconstructor = ConsoleReconstructor()
            reconstructor.feed(b"VPCS> ", ConsoleFrameSequenceData.T0)

        with autotest.step("Act: it sends the prompt again with the echoed command"):
            reconstructor.feed(b"VPCS> show ip\r\n", ConsoleFrameSequenceData.T0)
            commands = reconstructor.feed(b"VPCS> ", ConsoleFrameSequenceData.T0)

        with autotest.step("Assert: the command is stored without the repeated prompt"):
            assert_equal([c.command for c in commands], ["show ip"], "commands")
