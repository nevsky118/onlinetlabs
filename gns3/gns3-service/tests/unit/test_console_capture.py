"""Tests console capture and the console WS path parser."""

import asyncio
import uuid
from datetime import UTC, datetime

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from src.console_capture import (
    MAX_CONNECTION_BYTES,
    ConsoleCapture,
    ConsoleCommandRecord,
    ConsoleFrame,
    redact_secrets,
)
from src.db.models import ConsoleChunk, ConsoleCommand
from src.routers.console_ws import parse_console_path
from tests.settings.data.console_data import (
    ConsoleBlockingWriterData,
    ConsoleCaptureData,
    ConsoleClockData,
    ConsoleCommitGateData,
    ConsoleDbFactoryData,
    ConsoleRetentionDbData,
    ConsoleRetentionRowReaderData,
    ConsoleSecretLineData,
    ConsoleWriteBatchData,
)

pytestmark = [pytest.mark.unit]


class TestParseConsolePath:
    """Parses both GNS3 console URL shapes, rejects others."""

    @autotest.num("3513")
    @autotest.external_id("be51713d-cbab-4967-a23c-e6f311f72f69")
    @autotest.name("parse_console_path: controller-level URL yields project and node")
    def test_be51713d_controller_level_path(self):
        with autotest.step("Act"):
            parsed = parse_console_path("/v3/projects/proj-1/nodes/node-1/console/ws")

        with autotest.step("Assert"):
            assert_equal(parsed, ("proj-1", "node-1"), "parsed")

    @autotest.num("3514")
    @autotest.external_id("cd9d50e8-9f15-4178-9106-6f26ee11e91f")
    @autotest.name("parse_console_path: compute-level URL yields project and node")
    def test_cd9d50e8_compute_level_path(self):
        with autotest.step("Act"):
            parsed = parse_console_path("/v3/compute/projects/proj-2/nodes/node-2/console/ws")

        with autotest.step("Assert"):
            assert_equal(parsed, ("proj-2", "node-2"), "parsed")

    @autotest.num("3515")
    @autotest.external_id("64a8be37-913a-46ae-ac4f-984f9f2e1df5")
    @autotest.name("parse_console_path: a non-console path is rejected")
    def test_64a8be37_rejects_non_console_path(self):
        with autotest.step("Act + Assert"):
            assert_equal(parse_console_path("/v3/projects/proj-1/nodes"), None, "parsed")
            assert_equal(parse_console_path("/v3/projects/proj-1/notifications/ws"), None, "parsed")


class TestConsoleTapOrdering:
    """Both directions share one monotonic sequence."""

    @autotest.num("3516")
    @autotest.external_id("4ed27177-4bec-481b-bc45-55aaae34b488")
    @autotest.name("ConsoleTap: both directions share one monotonic sequence")
    def test_4ed27177_shared_sequence(self):
        with autotest.step("Arrange"):
            capture, tap = ConsoleCaptureData.build()

        with autotest.step("Act: interleave typed lines and node output"):
            tap.from_client(b"sh\r")
            tap.from_node(b"sh\r\n")
            tap.from_client(b"show\r")
            tap.from_node(b"show\r\n")

        with autotest.step("Assert: sequence counts up across directions"):
            frames = ConsoleCaptureData.drain(capture)
            assert_equal([f.seq for f in frames], [1, 2, 3, 4], "seq")
            assert_equal([f.direction for f in frames], ["in", "out", "in", "out"], "direction")

    @autotest.num("3517")
    @autotest.external_id("f3ac2aab-7e5f-49c0-8c84-d7845ab2085b")
    @autotest.name("ConsoleTap: an empty frame is not recorded")
    def test_f3ac2aab_empty_frame_skipped(self):
        with autotest.step("Arrange"):
            capture, tap = ConsoleCaptureData.build()

        with autotest.step("Act"):
            tap.from_client(b"")

        with autotest.step("Assert"):
            assert_equal(len(ConsoleCaptureData.drain(capture)), 0, "frames")

    @autotest.num("3518")
    @autotest.external_id("683861d9-145c-4eb0-b796-4b8de7b0e0bf")
    @autotest.name("ConsoleTap: capture stops once the connection byte budget is spent")
    def test_683861d9_byte_budget_stops_capture(self):
        with autotest.step("Arrange"):
            capture, tap = ConsoleCaptureData.build()

        with autotest.step("Act: exceed the budget, then send more"):
            tap.from_node(b"x" * (MAX_CONNECTION_BYTES + 1))
            ConsoleCaptureData.drain(capture)
            tap.from_node(b"still talking")

        with autotest.step("Assert: nothing is recorded after the budget is spent"):
            assert_equal(len(ConsoleCaptureData.drain(capture)), 0, "frames")


class TestRowBudget:
    """Caps a console's rows independent of byte size."""

    @autotest.num("3519")
    @autotest.external_id("649b43f9-36a5-4e5b-8f75-f81c298d042e")
    @autotest.name("ConsoleTap: capture stops once the row budget is spent")
    async def test_649b43f9_capture_stops_at_the_row_budget(self):
        with autotest.step("Arrange: a tap with a two-row budget"):
            capture, tap = ConsoleCaptureData.build()
            tap._max_rows = 2

        with autotest.step("Act: send five lines"):
            for _ in range(5):
                tap.from_node(b"a\r\n")

        with autotest.step("Assert: only the budget was recorded"):
            assert_equal(len(ConsoleCaptureData.drain(capture)), 2, "rows capped")


class TestPasswordRedaction:
    """Masks typed input after a password prompt."""

    @autotest.num("3520")
    @autotest.external_id("66c02c2c-bbf3-423e-b81d-754044ee70a3")
    @autotest.name("ConsoleTap: input after a password prompt is masked")
    def test_66c02c2c_masks_password_after_prompt(self):
        with autotest.step("Arrange: the node asks for a password"):
            capture, tap = ConsoleCaptureData.build()
            tap.from_node(b"\r\nPassword: ")
            ConsoleCaptureData.drain(capture)

        with autotest.step("Act: the learner types the secret, the socket closes"):
            tap.from_client(b"s3cret")
            tap.close()

        with autotest.step("Assert: stars are stored, length preserved"):
            frames = ConsoleCaptureData.drain(capture)
            assert_equal(frames[0].payload, b"******", "payload")
            assert_equal(frames[0].redacted, True, "redacted")

    @autotest.num("3521")
    @autotest.external_id("ce17e1a6-b388-431a-a323-9c4eb9f0cbf7")
    @autotest.name("ConsoleTap: masking stops at the newline that ends the password")
    def test_ce17e1a6_masking_stops_at_newline(self):
        with autotest.step("Arrange"):
            capture, tap = ConsoleCaptureData.build()
            tap.from_node(b"Password: ")
            ConsoleCaptureData.drain(capture)

        with autotest.step("Act: secret and newline arrive together, then a command"):
            tap.from_client(b"s3cret\r")
            tap.from_client(b"show ip route")
            tap.close()

        with autotest.step("Assert: only the secret is masked"):
            frames = ConsoleCaptureData.drain(capture)
            assert_equal(frames[0].payload, b"******\r", "masked payload")
            assert_equal(frames[1].payload, b"show ip route", "later command")
            assert_equal(frames[1].redacted, False, "later command not redacted")

    @autotest.num("3522")
    @autotest.external_id("807512df-1bb4-457e-91ad-72791cad9e38")
    @autotest.name("ConsoleTap: ordinary input is stored verbatim")
    def test_807512df_plain_input_not_masked(self):
        with autotest.step("Arrange"):
            capture, tap = ConsoleCaptureData.build()

        with autotest.step("Act"):
            tap.from_client(b"conf t\r")

        with autotest.step("Assert"):
            frames = ConsoleCaptureData.drain(capture)
            assert_equal(frames[0].payload, b"conf t\r", "payload")
            assert_equal(frames[0].redacted, False, "redacted")

    @autotest.num("3584")
    @autotest.external_id("3845aeff-874a-410e-b490-8d69babed392")
    @autotest.name("ConsoleTap: Enter on an empty password does not disarm masking")
    def test_3845aeff_empty_password_line_keeps_masking_armed(self):
        with autotest.step("Arrange: the node asks for a password"):
            capture, tap = ConsoleCaptureData.build()
            tap.from_node(b"\r\nPassword: ")
            ConsoleCaptureData.drain(capture)

        with autotest.step("Act: a stray carriage return leads the typed secret"):
            tap.from_client(b"\r\ns3cret\r\n")

        with autotest.step("Assert: the secret is starred, the line breaks kept"):
            frames = ConsoleCaptureData.drain(capture)
            assert_equal(frames[0].payload, b"\r\n******\r\n", "payload")
            assert_equal(frames[0].redacted, True, "redacted")


class TestQueueBackpressure:
    """A full queue drops frames instead of blocking."""

    @autotest.num("3523")
    @autotest.external_id("0a01448a-4fe3-47b8-98de-956a43effc62")
    @autotest.name("ConsoleCapture: submitting to a full queue drops and counts")
    def test_0a01448a_drops_when_full(self):
        with autotest.step("Arrange: a queue of one"):
            capture = ConsoleCapture(db_factory=None, queue_size=1)
            tap = capture.tap(uuid.uuid4(), "node-1")

        with autotest.step("Act: send two lines"):
            tap.from_client(b"a\r")
            tap.from_client(b"b\r")

        with autotest.step("Assert: one queued, one counted as dropped"):
            assert_equal(capture._queue.qsize(), 1, "queued")
            assert_equal(capture.dropped, 1, "dropped")


class TestQueueByteBudget:
    """Caps queue backlog at a byte budget."""

    @autotest.num("3524")
    @autotest.external_id("1ededc0b-ac1a-4ccc-881c-635913e2f441")
    @autotest.name("ConsoleCapture: submit drops once the byte budget is full")
    def test_1ededc0b_submit_drops_once_the_byte_budget_is_full(self):
        with autotest.step("Arrange: a capture allowed only 4 KiB of backlog"):
            capture = ConsoleCapture(db_factory=None, max_queue_bytes=4096)
            tap = capture.tap(uuid.uuid4(), "node-1")

        with autotest.step("Act: push 64 KiB of node output"):
            for _ in range(64):
                tap.from_node(b"x" * 1024)

        with autotest.step("Assert: the backlog is capped and the rest counted as dropped"):
            assert_true(capture.queued_bytes <= 4096, "byte budget held")
            assert_true(capture.dropped > 0, "overflow was dropped")


class TestProbeFiltering:
    """Filters platform probes out of learner commands."""

    @autotest.num("3525")
    @autotest.external_id("f736cb04-d8eb-4853-8843-d07ecfd10e9c")
    @autotest.name("ConsoleTap: a command the learner typed is recorded")
    def test_f736cb04_keeps_typed_command(self):
        with autotest.step("Arrange"):
            capture, tap = ConsoleCaptureData.build()

        with autotest.step("Act: type the command, then let the node echo it"):
            tap.from_client(b"show ip\r")
            tap.from_node(b"VPCS> show ip\r\n")
            tap.from_node(b"IP/MASK : 0.0.0.0/0\r\n")
            tap.from_node(b"VPCS> ")

        with autotest.step("Assert: the command is queued"):
            commands = [
                f for f in ConsoleCaptureData.drain(capture) if isinstance(f, ConsoleCommandRecord)
            ]
            assert_equal([c.command for c in commands], ["show ip"], "commands")

    @autotest.num("3526")
    @autotest.external_id("b8a1620f-a324-48a8-83cf-7be78002966d")
    @autotest.name("ConsoleTap: a probe nobody typed is dropped")
    def test_b8a1620f_drops_untyped_probe(self):
        with autotest.step("Arrange: no keystrokes at all on this socket"):
            capture, tap = ConsoleCaptureData.build()

        with autotest.step("Act: the platform's spec check echoes through the shared console"):
            tap.from_node(b"VPCS> show ip\r\n")
            tap.from_node(b"IP/MASK : 0.0.0.0/0\r\n")
            tap.from_node(b"VPCS> ")

        with autotest.step("Assert: nothing is recorded as a command"):
            commands = [
                f for f in ConsoleCaptureData.drain(capture) if isinstance(f, ConsoleCommandRecord)
            ]
            assert_equal(len(commands), 0, "commands")

    @autotest.num("3527")
    @autotest.external_id("6ba1b4fa-40d1-4015-a83f-9276365aa746")
    @autotest.name("ConsoleTap: one keypress claims one command, not the probes after it")
    def test_6ba1b4fa_one_enter_claims_one_command(self):
        with autotest.step("Arrange: the learner runs one command"):
            capture, tap = ConsoleCaptureData.build()
            tap.from_client(b"show ip\r")
            tap.from_node(b"VPCS> show ip\r\n")
            tap.from_node(b"VPCS> ")

        with autotest.step("Act: the platform then probes the same console twice"):
            tap.from_node(b"VPCS> show ip\r\n")
            tap.from_node(b"VPCS> ")
            tap.from_node(b"VPCS> ping 192.168.1.12\r\n")
            tap.from_node(b"VPCS> ")

        with autotest.step("Assert: only the learner's command survives"):
            commands = [
                f for f in ConsoleCaptureData.drain(capture) if isinstance(f, ConsoleCommandRecord)
            ]
            assert_equal([c.command for c in commands], ["show ip"], "commands")

    @autotest.num("3528")
    @autotest.external_id("ff95b414-e3d6-4e3a-940c-770f01cdf482")
    @autotest.name("ConsoleTap: a command recalled from history still counts as the learner's")
    def test_ff95b414_keeps_history_recall(self):
        with autotest.step("Arrange: up-arrow then Enter sends no letters of the command"):
            capture, tap = ConsoleCaptureData.build()

        with autotest.step("Act"):
            tap.from_client(b"\x1b[A")
            tap.from_client(b"\r")
            tap.from_node(b"VPCS> show ip\r\n")
            tap.from_node(b"VPCS> ")

        with autotest.step("Assert: matching on the keypress keeps it"):
            commands = [
                f for f in ConsoleCaptureData.drain(capture) if isinstance(f, ConsoleCommandRecord)
            ]
            assert_equal([c.command for c in commands], ["show ip"], "commands")

    @autotest.num("3529")
    @autotest.external_id("facfc22b-c678-41c6-b8f7-fdfaf5468114")
    @autotest.name("ConsoleTap: a bare Enter does not license a later probe")
    def test_facfc22b_bare_enter_does_not_claim_probe(self, monkeypatch):
        with autotest.step("Arrange: a controllable clock; the learner presses Enter"):
            ConsoleClockData.set(datetime(2026, 1, 1, tzinfo=UTC))
            monkeypatch.setattr("src.console_capture.datetime", ConsoleClockData)
            capture, tap = ConsoleCaptureData.build()
            tap.from_client(b"\r")
            tap.from_node(b"VPCS> \r\n")
            tap.from_node(b"VPCS> ")
            ConsoleCaptureData.drain(capture)

        with autotest.step("Act: the 2-second enter window passes, then a probe arrives"):
            ConsoleClockData.advance(3.0)
            tap.from_node(b"VPCS> show ip\r\n")
            tap.from_node(b"VPCS> ")

        with autotest.step("Assert: the probe is not attributed to the learner"):
            commands = [
                f for f in ConsoleCaptureData.drain(capture) if isinstance(f, ConsoleCommandRecord)
            ]
            assert_equal(len(commands), 0, "commands")


class TestSecretRedaction:
    """Redacts credentials echoed as command arguments."""

    @autotest.num("3530")
    @autotest.external_id("2db822e0-3e75-4772-b51d-7d8376bec3a6")
    @autotest.name("redact_secrets: credential arguments never reach the queue")
    async def test_2db822e0_secret_arguments_never_reach_the_queue(self):
        with autotest.step("Arrange: a capture with no database"):
            capture, tap = ConsoleCaptureData.build()

        with autotest.step("Act: the node echoes several secret-bearing commands"):
            tap.from_node(b"R1(config)#enable secret Cisco123\r\n")
            tap.from_node(b"R1(config)#username bob password s3cr3t\r\n")
            tap.from_node(b"R1(config)#snmp-server community public ro\r\n")
            tap.from_node(b"R1(config-keychain-key)#key-string MySecret123\r\n")
            tap.from_node(b"R1(config)#crypto isakmp key MyPsk address 1.2.3.4\r\n")
            tap.from_node(b"R1(config)#wlan security psk MyWifiSecret\r\n")

        with autotest.step("Assert: no secret survives in any queued payload"):
            payloads = b" ".join(
                frame.payload
                for frame in ConsoleCaptureData.drain(capture)
                if hasattr(frame, "payload")
            )
            secrets = (
                b"Cisco123",
                b"s3cr3t",
                b"public",
                b"MySecret123",
                b"MyPsk",
                b"MyWifiSecret",
            )
            for secret in secrets:
                assert_true(secret not in payloads, f"secret {secret.decode()} redacted")

    @autotest.num("3531")
    @autotest.external_id("0e431136-bcb8-4f08-a3a3-f37a53e7fd8e")
    @autotest.name("redact_secrets: a benign use of 'authentication' is not redacted")
    async def test_0e431136_benign_authentication_word_not_redacted(self):
        with autotest.step("Arrange: a capture with no database"):
            capture, tap = ConsoleCaptureData.build()

        with autotest.step("Act: the node echoes a non-credential authentication command"):
            tap.from_node(b"R1(config-if)#ppp authentication chap\r\n")

        with autotest.step("Assert: the command survives unredacted"):
            payloads = b" ".join(
                frame.payload
                for frame in ConsoleCaptureData.drain(capture)
                if hasattr(frame, "payload")
            )
            assert_true(
                b"ppp authentication chap" in payloads,
                "benign authentication keyword left untouched",
            )

    @autotest.num("3532")
    @autotest.external_id("2c68582b-ec38-467b-880e-1517baaf250d")
    @autotest.name("redact_secrets: a keyword with no argument does not consume the next line")
    def test_2c68582b_secret_match_does_not_cross_a_newline(self):
        with autotest.step("Act: 'key' ends its line, the argument is really the next command"):
            redacted, secret_found = redact_secrets(b"key\r\nnext_command_here\r\n")

        with autotest.step("Assert: nothing is touched, the next line survives verbatim"):
            assert_equal(redacted, b"key\r\nnext_command_here\r\n", "payload")
            assert_true(not secret_found, "no match spans the newline")

    @autotest.num("3533")
    @autotest.external_id("c1005bf9-cb90-48ae-8303-68c9a225a71a")
    @autotest.name("redact_secrets: two prompt lines are not merged into one match")
    def test_c1005bf9_secret_does_not_merge_two_prompt_lines(self):
        with autotest.step("Act: a bare 'secret' keyword precedes a second command's line"):
            data = b"R1(config)#enable secret\r\nR1(config)#username bob password s3cr3t\r\n"
            redacted, secret_found = redact_secrets(data)

        with autotest.step("Assert: the first line is untouched, only the second is redacted"):
            assert_equal(
                redacted,
                b"R1(config)#enable secret\r\nR1(config)#username bob password ***\r\n",
                "payload",
            )
            assert_true(secret_found, "the second line's secret was redacted")

    @autotest.num("3534")
    @autotest.external_id("a7e3b847-3487-4a34-95b6-8cdaae339273")
    @autotest.name("redact_secrets: a running-config response is redacted before queueing")
    async def test_a7e3b847_command_response_is_redacted(self):
        with autotest.step("Arrange: a capture with no database"):
            capture, tap = ConsoleCaptureData.build()

        with autotest.step("Act: the learner runs show running-config"):
            tap.from_client(b"show running-config\r")
            tap.from_node(b"R1#show running-config\r\n")
            tap.from_node(b"enable secret Cisco123\r\n")
            tap.from_node(b"username bob password s3cr3t\r\n")
            tap.from_node(b"R1#")

        with autotest.step("Assert: no secret survives in the queued response"):
            commands = [
                f for f in ConsoleCaptureData.drain(capture) if isinstance(f, ConsoleCommandRecord)
            ]
            responses = " ".join(command.response for command in commands)
            for secret in ("Cisco123", "s3cr3t"):
                assert_true(secret not in responses, f"response secret {secret} redacted")


class TestDrainKeepsUp:
    @autotest.num("3535")
    @autotest.external_id("d7a88042-b9b0-4900-baa4-76a7eb320c29")
    @autotest.name("ConsoleCapture: one drain writes everything queued")
    async def test_d7a88042_drain_writes_everything_queued(self):
        with autotest.step("Arrange: a capture whose writes are recorded"):
            written: list = []

            async def record_batch(batch):
                written.extend(batch)

            capture = ConsoleCapture(db_factory=None, batch_size=200)
            capture._db_factory = object()
            capture._write = record_batch

        with autotest.step("Act: queue five batches worth and drain once"):
            tap = capture.tap(uuid.uuid4(), "node-1")
            for index in range(1000):
                tap.from_node(b"line %d\r\n" % index)
            await capture._drain_once()

        with autotest.step("Assert: nothing is left behind"):
            assert_equal(capture._queue.qsize(), 0, "queue drained")
            assert_equal(len(written), 1000, "every frame written")
            assert_equal(capture.queued_bytes, 0, "byte budget released")


class TestWriteResilience:
    """A failed chunk commit does not block the command commit."""

    @autotest.num("3536")
    @autotest.external_id("29754b7f-deea-454b-a4c3-91da469a028d")
    @autotest.name("ConsoleCapture._write: a failed chunk commit still lets commands land")
    async def test_29754b7f_failed_chunk_commit_does_not_lose_command_rows(self, caplog):
        with autotest.step("Arrange: a batch of one chunk and one command"):
            db_factory = ConsoleDbFactoryData(fail_first=True)
            capture = ConsoleCapture(db_factory=db_factory)
            session_id = uuid.uuid4()
            connection_id = uuid.uuid4()
            frame = ConsoleFrame(
                session_id=session_id,
                node_id="node-1",
                connection_id=connection_id,
                seq=1,
                direction="out",
                payload=b"hello",
                truncated=False,
                redacted=False,
                ts=datetime.now(UTC),
            )
            command = ConsoleCommandRecord(
                session_id=session_id,
                node_id="node-1",
                connection_id=connection_id,
                seq=1,
                prompt="R1#",
                command="show ip",
                response="1.1.1.1",
                ts=datetime.now(UTC),
                duration_ms=1.0,
            )

        with autotest.step("Act: write the batch while the chunk commit fails"):
            with caplog.at_level("ERROR"):
                await capture._write([frame, command])

        with autotest.step("Assert: the chunk commit fired and failed, the command commit landed"):
            assert_equal(len(db_factory.sessions), 2, "two transactions opened")
            assert_equal(db_factory.sessions[0].commit_attempts, 1, "chunk commit was attempted")
            assert_equal(db_factory.sessions[0].committed, [], "chunk commit did not land")
            assert_equal(db_factory.sessions[1].commit_attempts, 1, "command commit fired")
            assert_equal(len(db_factory.sessions[1].committed), 1, "command row committed")
            assert_equal(
                db_factory.sessions[1].committed[0].command,
                "show ip",
                "committed row carries the command",
            )
            assert_true(
                any("chunk rows" in record.message for record in caplog.records),
                "chunk commit failure logged",
            )


class TestPastedBlock:
    """A pasted block arrives as one multi-line frame."""

    @autotest.num("3537")
    @autotest.external_id("fbda8a71-1681-4a2b-80e2-606fec6d390d")
    @autotest.name("ConsoleTap: every line of a pasted block is attributed")
    def test_fbda8a71_every_line_of_a_pasted_block_is_attributed(self):
        with autotest.step("Arrange: a tap"):
            capture, tap = ConsoleCaptureData.build()

        with autotest.step("Act: the learner pastes three lines in one frame"):
            tap.from_client(b"interface eth0\r\nip address 10.0.0.1/24\r\nno shutdown\r\n")

        with autotest.step("Assert: three keypresses are pending, not one"):
            assert_equal(len(tap._pending_enters), 3, "one per line")

    @autotest.num("3538")
    @autotest.external_id("9df654c1-2022-4e86-9826-334cbc6f445a")
    @autotest.name("ConsoleTap: a forty-line paste keeps every pending keypress")
    def test_9df654c1_forty_line_paste_keeps_every_pending_keypress(self):
        with autotest.step("Arrange: a tap"):
            capture, tap = ConsoleCaptureData.build()

        with autotest.step("Act: the learner pastes a forty-line block in one frame"):
            block = b"".join(b"line %d\r\n" % i for i in range(40))
            tap.from_client(block)

        with autotest.step("Assert: all forty keypresses are pending, none evicted by the cap"):
            assert_equal(len(tap._pending_enters), 40, "one per line")

    @autotest.num("3581")
    @autotest.external_id("631073fe-21e5-412a-9025-c41c6bc4cb94")
    @autotest.name("ConsoleTap: a syslog message between echoes costs the paste no command")
    def test_631073fe_syslog_between_echoes_keeps_every_pasted_command(self):
        with autotest.step("Arrange: the learner pastes three commands"):
            capture, tap = ConsoleCaptureData.build()
            tap.from_client(b"show ip\rshow ver\rshow run\r")

        with autotest.step("Act: the node redraws its prompt for an unsolicited syslog line"):
            tap.from_node(b"VPCS> show ip\r\n")
            tap.from_node(b"IP/MASK : 0.0.0.0/0\r\n")
            tap.from_node(b"VPCS> \r\n")
            tap.from_node(b"*Mar  1 00:00:00: %LINK-3-UPDOWN: Interface up\r\n")
            tap.from_node(b"VPCS> show ver\r\n")
            tap.from_node(b"VPCS> show run\r\n")
            tap.from_node(b"VPCS> ")

        with autotest.step("Assert: all three commands are stored"):
            commands = [
                item
                for item in ConsoleCaptureData.drain(capture)
                if isinstance(item, ConsoleCommandRecord)
            ]
            assert_equal(
                [command.command for command in commands],
                ["show ip", "show ver", "show run"],
                "commands",
            )


class TestPromptTruncation:
    """A long prompt is truncated, not fatal."""

    @autotest.num("3539")
    @autotest.external_id("b890032d-1860-43ef-8292-8abe4ff66191")
    @autotest.name("ConsoleTap: a long prompt is truncated, not fatal")
    def test_b890032d_a_long_prompt_is_truncated_not_fatal(self):
        with autotest.step("Arrange: a tap and a 500 character prompt"):
            capture, tap = ConsoleCaptureData.build()

        with autotest.step("Act: the learner runs a command under the long prompt"):
            tap.from_client(b"show version\r")
            tap.from_node(("R" * 500 + "#show version\r\n").encode())
            tap.from_node(b"IOS 15.2\r\n" + ("R" * 500 + "#").encode())

        with autotest.step("Assert: the stored prompt fits the column"):
            commands = [
                item
                for item in ConsoleCaptureData.drain(capture)
                if isinstance(item, ConsoleCommandRecord)
            ]
            assert_true(len(commands) > 0, "a command was captured")
            for command in commands:
                assert_true(len(command.prompt or "") <= 255, "prompt fits")


class TestNodeIdClamp:
    """An oversized node id is clamped to fit."""

    @autotest.num("3540")
    @autotest.external_id("c9dddf51-f826-40da-b54b-8b98c910f749")
    @autotest.name("ConsoleTap: an over-length node id is clamped to the column width")
    def test_c9dddf51_over_length_node_id_is_clamped(self):
        with autotest.step("Arrange: a tap built with a 500 character node id"):
            capture, tap = ConsoleCaptureData.build(node_id="N" * 500)

        with autotest.step("Act: the tap records a frame and a command"):
            tap.from_client(b"show ip\r")
            tap.from_node(b"VPCS> show ip\r\n")
            tap.from_node(b"VPCS> ")

        with autotest.step("Assert: every queued row's node_id fits the column"):
            items = ConsoleCaptureData.drain(capture)
            assert_true(len(items) > 0, "rows were queued")
            for item in items:
                assert_equal(len(item.node_id), 64, "node_id clamped")


class TestPasteAttributionOverTime:
    """A slow-echoing paste is still attributed to the learner."""

    @autotest.num("3541")
    @autotest.external_id("b40346f3-eb6e-4c76-bf04-bdceb4e4b42a")
    @autotest.name("ConsoleTap: a slow-echoing paste keeps every line attributed")
    def test_b40346f3_slow_echo_keeps_every_pasted_line_attributed(self, monkeypatch):
        with autotest.step("Arrange: a controllable clock and a tap"):
            ConsoleClockData.set(datetime(2026, 1, 1, tzinfo=UTC))
            monkeypatch.setattr("src.console_capture.datetime", ConsoleClockData)
            capture, tap = ConsoleCaptureData.build()

        with autotest.step("Act: paste five lines, node echoes one every 1.5s (6s total)"):
            lines = [
                b"interface eth0",
                b"ip address 10.0.0.1/24",
                b"no shutdown",
                b"description uplink",
                b"exit",
            ]
            tap.from_client(b"\r\n".join(lines) + b"\r\n")
            for line in lines:
                ConsoleClockData.advance(1.5)
                tap.from_node(b"R1(config)#" + line + b"\r\n")
            tap.from_node(b"R1(config)#")

        with autotest.step("Assert: all five lines survive, none dropped as a stale probe"):
            commands = [
                f for f in ConsoleCaptureData.drain(capture) if isinstance(f, ConsoleCommandRecord)
            ]
            assert_equal(
                [c.command for c in commands],
                [line.decode() for line in lines],
                "commands",
            )

    @autotest.num("3542")
    @autotest.external_id("a57b9c48-f05c-4785-bd1a-b9f20e37f15a")
    @autotest.name("ConsoleTap: a paste with no echo at all still expires")
    def test_a57b9c48_stale_paste_does_not_claim_a_late_probe(self, monkeypatch):
        with autotest.step("Arrange: a controllable clock and a tap"):
            ConsoleClockData.set(datetime(2026, 1, 1, tzinfo=UTC))
            monkeypatch.setattr("src.console_capture.datetime", ConsoleClockData)
            capture, tap = ConsoleCaptureData.build()

        with autotest.step("Act: paste three lines, nothing echoes for 3s, then a probe does"):
            tap.from_client(b"interface eth0\r\nip address 10.0.0.1/24\r\nno shutdown\r\n")
            ConsoleClockData.advance(3.0)
            tap.from_node(b"R1(config)#show ip route\r\n")
            tap.from_node(b"R1(config)#")

        with autotest.step("Assert: the probe is not attributed to the learner"):
            commands = [
                f for f in ConsoleCaptureData.drain(capture) if isinstance(f, ConsoleCommandRecord)
            ]
            assert_equal(len(commands), 0, "commands")


class TestWriteReachesTheDatabase:
    """_write turns frames and commands into real rows."""

    @autotest.num("3560")
    @autotest.external_id("cf5b9706-09e3-4963-97b0-c6b506a619fc")
    @autotest.name("ConsoleCapture._write: a frame and a command land in the real tables")
    async def test_cf5b9706_frame_and_command_land_in_the_real_tables(self):
        with autotest.step("Arrange: a capture over a real sqlite database"):
            db_factory = await ConsoleRetentionDbData.factory(
                [ConsoleChunk.__table__, ConsoleCommand.__table__]
            )
            session_id = uuid.uuid4()
            capture = ConsoleCapture(db_factory=db_factory)
            tap = capture.tap(session_id, "node-1")

        with autotest.step("Act: type a command, echo a secret-bearing response, drain"):
            tap.from_client(b"show version\r")
            tap.from_node(("R" * 500 + "#show version\r\n").encode())
            tap.from_node(b"enable secret Cisco123\r\n" + ("R" * 500 + "#").encode())
            await capture._drain_once()

        with autotest.step("Assert: the typed keystroke is a real console_chunks row"):
            chunks = await ConsoleRetentionRowReaderData.chunks(db_factory)
            typed = next(row for row in chunks if row.direction == "in")
            assert_equal(typed.direction, "in", "direction stored")
            assert_equal(typed.payload, b"show version\r", "payload bytes stored verbatim")
            assert_equal(typed.session_id, session_id, "session id round-trips through sqlite")

        with autotest.step("Assert: the command is a real console_commands row"):
            commands = await ConsoleRetentionRowReaderData.commands(db_factory)
            assert_equal(len(commands), 1, "one command row")
            stored = commands[0]
            assert_equal(stored.command, "show version", "command text stored")
            assert_equal(len(stored.prompt or ""), 255, "prompt clamped to the column width")
            assert_true("Cisco123" not in stored.response, "redacted secret absent from response")


class TestFrameBuffering:
    """Buffers byte-at-a-time input into whole lines."""

    @autotest.num("3567")
    @autotest.external_id("f9dbb564-75cd-47e4-9765-18d155397df7")
    @autotest.name("ConsoleTap: a secret split across one-byte frames is still redacted")
    def test_f9dbb564_secret_split_across_frames_is_redacted(self):
        with autotest.step("Arrange: a capture with no database"):
            capture, tap = ConsoleCaptureData.build()

        with autotest.step("Act: the node echoes a credential one byte per frame"):
            for byte in b"R1(config)#enable secret cisco123\r\n":
                tap.from_node(bytes([byte]))

        with autotest.step("Assert: the secret never reaches a queued payload"):
            payloads = b"".join(
                frame.payload
                for frame in ConsoleCaptureData.drain(capture)
                if hasattr(frame, "payload")
            )
            assert_true(b"cisco123" not in payloads, "secret redacted across frames")
            assert_true(b"***" in payloads, "the line was masked, not dropped")

    @autotest.num("3568")
    @autotest.external_id("36cb35ae-e20e-4244-9cd7-2e83b7f9c8e0")
    @autotest.name("ConsoleTap: a buffered frame is timestamped by its first byte")
    def test_36cb35ae_buffered_frame_carries_the_first_byte_timestamp(self, monkeypatch):
        with autotest.step("Arrange: a controllable clock and a tap"):
            start = datetime(2026, 1, 1, tzinfo=UTC)
            ConsoleClockData.set(start)
            monkeypatch.setattr("src.console_capture.datetime", ConsoleClockData)
            capture, tap = ConsoleCaptureData.build()

        with autotest.step("Act: half a line, five seconds, then the rest of it"):
            tap.from_node(b"abc")
            ConsoleClockData.advance(5.0)
            tap.from_node(b"def\r\n")

        with autotest.step("Assert: one frame holding the whole line, stamped at its start"):
            frames = ConsoleCaptureData.drain(capture)
            assert_equal(len(frames), 1, "frames")
            assert_equal(frames[0].payload, b"abcdef\r\n", "payload")
            assert_equal(frames[0].ts, start, "ts")

    @autotest.num("3569")
    @autotest.external_id("d0dc31ba-e22f-439b-826d-4f4827cb3ed0")
    @autotest.name("ConsoleTap: close flushes the unterminated bytes of both directions")
    def test_d0dc31ba_close_flushes_both_direction_buffers(self):
        with autotest.step("Arrange: a tap holding an unfinished line each way"):
            capture, tap = ConsoleCaptureData.build()
            tap.from_client(b"conf t")
            tap.from_node(b"R1#conf")

        with autotest.step("Act: the socket goes away"):
            tap.close()

        with autotest.step("Assert: both buffers were stored, typed direction first"):
            frames = [
                item for item in ConsoleCaptureData.drain(capture) if isinstance(item, ConsoleFrame)
            ]
            assert_equal(
                [(frame.direction, frame.payload) for frame in frames],
                [("in", b"conf t"), ("out", b"R1#conf")],
                "flushed frames",
            )


class TestSecretModifiers:
    """A modifier between keyword and secret still redacts."""

    @autotest.num("3570")
    @autotest.external_id("ce6c28c6-fa8d-4871-b270-9b0eed0946ee")
    @autotest.name("redact_secrets: separators and modifiers do not shield the secret")
    def test_ce6c28c6_modifiers_do_not_shield_the_secret(self):
        with autotest.step("Act + Assert: every credential form loses its value"):
            for line, secret in ConsoleSecretLineData.MUST_REDACT:
                redacted, secret_found = redact_secrets(line)
                assert_true(
                    secret not in redacted, f"{secret.decode()} redacted in {line.decode()}"
                )
                assert_true(secret_found, f"redaction reported for {line.decode()}")
                assert_true(b"***" in redacted, f"stars stored for {line.decode()}")

    @autotest.num("3580")
    @autotest.external_id("5a61095d-6866-47a5-bfd7-e6296f925282")
    @autotest.name("redact_secrets: a key keyword used for configuration is left alone")
    def test_5a61095d_configuration_keywords_are_not_erased(self):
        with autotest.step("Act + Assert: benign lines the validator grades from survive"):
            for line in ConsoleSecretLineData.MUST_KEEP:
                redacted, secret_found = redact_secrets(line)
                assert_equal(redacted, line, f"{line.decode()} untouched")
                assert_true(not secret_found, f"no redaction reported for {line.decode()}")


class TestStopKeepsTheInFlightBatch:
    """Stop still writes the batch it interrupted."""

    @autotest.num("3576")
    @autotest.external_id("cdd34651-3590-4f0d-9129-1653ac93ba6d")
    @autotest.name("ConsoleCapture.stop: a batch cancelled mid-write is written afterwards")
    async def test_cdd34651_stop_rewrites_the_cancelled_batch(self):
        with autotest.step("Arrange: a running capture whose first write blocks"):
            capture = ConsoleCapture(db_factory=None, flush_interval=0.01)
            capture._db_factory = object()
            writer = ConsoleBlockingWriterData()
            capture._write = writer
            await capture.start()
            tap = capture.tap(uuid.uuid4(), "node-1")

        with autotest.step("Act: queue a line, wait for the flusher to block, then stop"):
            tap.from_node(b"line one\r\n")
            await asyncio.wait_for(writer.entered.wait(), 2.0)
            await capture.stop()

        with autotest.step("Assert: the dequeued batch reached the writer after all"):
            assert_equal(len(writer.written), 1, "rows written")
            assert_equal(writer.written[0].payload, b"line one\r\n", "payload")


class TestInFlightHalves:
    """A replay repeats only the half that failed."""

    @autotest.num("3582")
    @autotest.external_id("2245db66-8d3f-4aae-a34d-47d0a2ee7cc1")
    @autotest.name("ConsoleCapture: a cancellation between the two commits writes no row twice")
    async def test_2245db66_cancellation_between_commits_does_not_repeat_chunks(self):
        with autotest.step("Arrange: a capture whose command commit hangs"):
            gate = ConsoleCommitGateData(block_commit=2)
            capture = ConsoleCapture(db_factory=gate, flush_interval=0.01)
            ConsoleWriteBatchData.submit(capture)

        with autotest.step("Act: run until the chunks are committed, then stop"):
            await capture.start()
            await asyncio.wait_for(gate.reached.wait(), 2.0)
            await capture.stop()

        with autotest.step("Assert: one row of each kind, the committed chunk not repeated"):
            assert_equal(gate.count(ConsoleChunk), 1, "chunk rows")
            assert_equal(gate.count(ConsoleCommand), 1, "command rows")

    @autotest.num("3583")
    @autotest.external_id("ed8912a6-84d8-42cf-8fb0-36379cc5d5b5")
    @autotest.name("ConsoleCapture: a cancellation before the first commit replays both halves")
    async def test_ed8912a6_cancellation_before_the_first_commit_replays_the_batch(self):
        with autotest.step("Arrange: a capture whose chunk commit hangs"):
            gate = ConsoleCommitGateData(block_commit=1)
            capture = ConsoleCapture(db_factory=gate, flush_interval=0.01)
            ConsoleWriteBatchData.submit(capture)

        with autotest.step("Act: run until the chunk commit blocks, then stop"):
            await capture.start()
            await asyncio.wait_for(gate.reached.wait(), 2.0)
            await capture.stop()

        with autotest.step("Assert: nothing was lost and nothing was doubled"):
            assert_equal(gate.count(ConsoleChunk), 1, "chunk rows")
            assert_equal(gate.count(ConsoleCommand), 1, "command rows")
