"""Builds console capture test doubles and fixtures."""

import asyncio
import importlib.util
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.console_capture import ConsoleCapture, ConsoleCommandRecord, ConsoleFrame, ConsoleTap
from src.db.models import ConsoleChunk, ConsoleCommand, SessionStatus
from src.db.models import Session as SessionModel
from src.routers.console_ws import console_ws


class ConsoleCaptureData:
    """A capture with no database, frames stay queued."""

    @staticmethod
    def build(node_id: str = "node-1") -> tuple[ConsoleCapture, ConsoleTap]:
        """A fresh capture and a tap on it."""
        capture = ConsoleCapture(db_factory=None)
        tap = capture.tap(uuid.uuid4(), node_id)
        return capture, tap

    @staticmethod
    def drain(capture: ConsoleCapture) -> list:
        """Everything currently queued, removed from the queue."""
        items = []
        while not capture._queue.empty():
            items.append(capture._queue.get_nowait())
        return items


class ConsoleClockData(datetime):
    """Stands in for console_capture's datetime.now, moved forward by hand."""

    _current: datetime

    @classmethod
    def now(cls, tz=None):
        return cls._current

    @classmethod
    def set(cls, value: datetime) -> None:
        cls._current = value

    @classmethod
    def advance(cls, seconds: float) -> None:
        cls._current = cls._current + timedelta(seconds=seconds)


class ConsoleDbSessionData:
    """Fake async db session that can fail its commit."""

    def __init__(self, fail_commit: bool) -> None:
        self._fail_commit = fail_commit
        self.added: list = []
        self.committed: list = []
        self.commit_attempts = 0

    async def __aenter__(self) -> "ConsoleDbSessionData":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    def add_all(self, rows: list) -> None:
        self.added.extend(rows)

    async def commit(self) -> None:
        self.commit_attempts += 1
        if self._fail_commit:
            raise RuntimeError("commit failed")
        self.committed.extend(self.added)


class ConsoleDbFactoryData:
    """Fake session factory; each call opens one session."""

    def __init__(self, fail_first: bool) -> None:
        self._fail_first = fail_first
        self.sessions: list[ConsoleDbSessionData] = []

    def __call__(self) -> ConsoleDbSessionData:
        session = ConsoleDbSessionData(fail_commit=self._fail_first and not self.sessions)
        self.sessions.append(session)
        return session


class ConsoleFrameSequenceData:
    """A fixed timestamp and spaced `out` frames."""

    T0 = datetime(2026, 9, 9, 12, 0, 0, tzinfo=UTC)

    @classmethod
    def out(cls, *payloads: bytes, step_ms: int = 100) -> list:
        """Builds `out` frames, one step apart."""
        return [
            ("out", payload, cls.T0 + timedelta(milliseconds=step_ms * i))
            for i, payload in enumerate(payloads)
        ]


class ConsoleWsSessionRowData:
    """Builds a Session row for _resolve_session tests."""

    @staticmethod
    def build(
        session_id: uuid.UUID, status: SessionStatus, created_at: datetime, project_id: str
    ) -> SessionModel:
        return SessionModel(
            id=session_id,
            gns3_user_id="user-1",
            gns3_username="learner",
            gns3_project_id=project_id,
            student_user_id="student-1",
            status=status,
            created_at=created_at,
        )


class ConsoleWsAppData:
    """FastAPI app seeded with the given Session rows."""

    @staticmethod
    async def build(sessions: list[SessionModel]) -> FastAPI:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.execute(text("PRAGMA foreign_keys = OFF"))
            await conn.run_sync(SessionModel.__table__.create)
        db_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with db_factory() as db:
            for session in sessions:
                db.add(session)
            await db.commit()

        app = FastAPI()
        app.state.db_factory = db_factory
        return app


class ConsoleWsSessionScenarioData:
    """FastAPI app with two sessions on one project."""

    OLDER = datetime(2026, 1, 1, tzinfo=UTC)
    NEWER = OLDER + timedelta(hours=1)

    @staticmethod
    async def build(project_id: str, older_status: SessionStatus) -> tuple[FastAPI, uuid.UUID]:
        newer_id = uuid.uuid4()
        app = await ConsoleWsAppData.build(
            [
                ConsoleWsSessionRowData.build(
                    uuid.uuid4(), older_status, ConsoleWsSessionScenarioData.OLDER, project_id
                ),
                ConsoleWsSessionRowData.build(
                    newer_id,
                    SessionStatus.ACTIVE,
                    ConsoleWsSessionScenarioData.NEWER,
                    project_id,
                ),
            ]
        )
        return app, newer_id


class StalledClientSocketData:
    """Stands in for the learner's WebSocket; receive() never returns."""

    def __init__(self, path: str) -> None:
        self.url = SimpleNamespace(path=path, query="")
        self.scope: dict = {}
        self.app = SimpleNamespace(state=SimpleNamespace())
        self.closed = False
        self.cancelled = False

    async def accept(self, subprotocol: str | None = None) -> None:
        return None

    async def receive(self):
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            self.cancelled = True
            raise

    async def send_text(self, text: str) -> None:
        return None

    async def send_bytes(self, data: bytes) -> None:
        return None

    async def close(self) -> None:
        self.closed = True


class StalledUpstreamSocketData:
    """Stands in for the gns3-server console socket; iteration never yields."""

    def __init__(self) -> None:
        self.subprotocol = None
        self.closed = False
        self.cancelled = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            self.cancelled = True
            raise

    async def send(self, data) -> None:
        return None

    async def close(self) -> None:
        self.closed = True


class StalledConsoleProxyData:
    """A console_ws handler over two fake sockets."""

    @staticmethod
    def build(monkeypatch: pytest.MonkeyPatch):
        """Unstarted handler plus the fake client and upstream sockets."""
        client = StalledClientSocketData("/v3/projects/proj-1/nodes/node-1/console/ws")
        upstream = StalledUpstreamSocketData()

        async def fake_connect(*args, **kwargs):
            return upstream

        monkeypatch.setattr("src.routers.console_ws.websockets.connect", fake_connect)
        handler = console_ws(client, "")
        return handler, client, upstream


class ConsoleRetentionSessionRowData:
    """Builds a Session row for purge_console_history tests."""

    @staticmethod
    def build(session_id: uuid.UUID, status: SessionStatus) -> SessionModel:
        return SessionModel(
            id=session_id,
            gns3_user_id="user-1",
            gns3_username="learner",
            gns3_project_id="project-1",
            student_user_id="student-1",
            status=status,
        )


class ConsoleChunkRowData:
    """Builds a ConsoleChunk row for purge_console_history tests."""

    @staticmethod
    def build(row_id: uuid.UUID, session_id: uuid.UUID, seq: int, ts: datetime) -> ConsoleChunk:
        return ConsoleChunk(
            id=row_id,
            session_id=session_id,
            node_id="node-1",
            connection_id=uuid.uuid4(),
            seq=seq,
            direction="out",
            payload=b"data",
            ts=ts,
        )


class ConsoleCommandRowData:
    """Builds a ConsoleCommand row for purge_console_history tests."""

    @staticmethod
    def build(row_id: uuid.UUID, session_id: uuid.UUID, seq: int, ts: datetime) -> ConsoleCommand:
        return ConsoleCommand(
            id=row_id,
            session_id=session_id,
            node_id="node-1",
            connection_id=uuid.uuid4(),
            seq=seq,
            prompt=None,
            command="show ip",
            response="ok",
            ts=ts,
        )


class ConsoleRetentionDbData:
    """In-memory sqlite session factory for the given ORM tables."""

    @staticmethod
    async def factory(tables) -> async_sessionmaker:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.execute(text("PRAGMA foreign_keys = OFF"))
            for table in tables:
                await conn.run_sync(table.create)
        return async_sessionmaker(engine, expire_on_commit=False)

    @staticmethod
    async def dispose(db_factory: async_sessionmaker) -> None:
        """Closes the engine behind the factory."""
        await db_factory.kw["bind"].dispose()


class ConsoleRetentionRowReaderData:
    """Reads back console rows for assertions."""

    @staticmethod
    async def chunk_ids(db_factory: async_sessionmaker) -> list:
        async with db_factory() as db:
            result = await db.execute(select(ConsoleChunk.id))
            return list(result.scalars())

    @staticmethod
    async def command_ids(db_factory: async_sessionmaker) -> list:
        async with db_factory() as db:
            result = await db.execute(select(ConsoleCommand.id))
            return list(result.scalars())

    @staticmethod
    async def chunks(db_factory: async_sessionmaker) -> list[ConsoleChunk]:
        async with db_factory() as db:
            result = await db.execute(select(ConsoleChunk).order_by(ConsoleChunk.seq))
            return list(result.scalars())

    @staticmethod
    async def commands(db_factory: async_sessionmaker) -> list[ConsoleCommand]:
        async with db_factory() as db:
            result = await db.execute(select(ConsoleCommand).order_by(ConsoleCommand.seq))
            return list(result.scalars())


class ConsoleRetentionSweepWatchData:
    """Signals when the retention sweep has finished."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from src import console_retention

        self.done = asyncio.Event()
        self.sweeps = 0
        original = console_retention.purge_console_history

        async def watched_purge(db_factory, older_than):
            removed = await original(db_factory, older_than)
            self.sweeps += 1
            self.done.set()
            return removed

        monkeypatch.setattr(console_retention, "purge_console_history", watched_purge)


class ConsoleRetentionScenarioData:
    """Seeded consoles-history scenarios for purge_console_history tests."""

    OLD_TS = datetime.now(UTC) - timedelta(days=10)
    FRESH_TS = datetime.now(UTC)

    @staticmethod
    async def with_old_and_fresh_rows() -> tuple[async_sessionmaker, uuid.UUID, uuid.UUID]:
        """An old and fresh row per table, closed session."""
        factory = await ConsoleRetentionDbData.factory(
            [SessionModel.__table__, ConsoleChunk.__table__, ConsoleCommand.__table__]
        )
        session_id = uuid.uuid4()
        old_chunk_id = uuid.uuid4()
        fresh_chunk_id = uuid.uuid4()
        old_command_id = uuid.uuid4()
        fresh_command_id = uuid.uuid4()
        async with factory() as db:
            db.add(ConsoleRetentionSessionRowData.build(session_id, SessionStatus.CLOSED))
            db.add(
                ConsoleChunkRowData.build(
                    old_chunk_id, session_id, 1, ConsoleRetentionScenarioData.OLD_TS
                )
            )
            db.add(
                ConsoleChunkRowData.build(
                    fresh_chunk_id, session_id, 2, ConsoleRetentionScenarioData.FRESH_TS
                )
            )
            db.add(
                ConsoleCommandRowData.build(
                    old_command_id, session_id, 1, ConsoleRetentionScenarioData.OLD_TS
                )
            )
            db.add(
                ConsoleCommandRowData.build(
                    fresh_command_id, session_id, 2, ConsoleRetentionScenarioData.FRESH_TS
                )
            )
            await db.commit()
        return factory, fresh_chunk_id, fresh_command_id

    @staticmethod
    async def with_one_old_row_on_an_active_session() -> tuple[async_sessionmaker, uuid.UUID]:
        """One old chunk row on a still-active session."""
        factory = await ConsoleRetentionDbData.factory(
            [SessionModel.__table__, ConsoleChunk.__table__, ConsoleCommand.__table__]
        )
        session_id = uuid.uuid4()
        row_id = uuid.uuid4()
        async with factory() as db:
            db.add(ConsoleRetentionSessionRowData.build(session_id, SessionStatus.ACTIVE))
            db.add(
                ConsoleChunkRowData.build(
                    row_id, session_id, 1, ConsoleRetentionScenarioData.OLD_TS
                )
            )
            await db.commit()
        return factory, row_id


class ConsoleSecretLineData:
    """Credential lines paired with the token to redact."""

    MUST_REDACT = (
        (b"wpa-psk ascii MySecret", b"MySecret"),
        (b"set password = topsecret", b"topsecret"),
        (b"ip ospf message-digest-key 1 md5 PASS", b"PASS"),
        (b"ntp authentication-key 1 md5 PASS", b"PASS"),
        (b"password: letmein", b"letmein"),
        (b"enable secret cisco123", b"cisco123"),
        (b"username bob password 7 08701E1D", b"08701E1D"),
        (b"key-string mysecret", b"mysecret"),
        (b"snmp-server community public RO", b"public"),
        (b"pre-shared-key address 1.2.3.4 key SECRET", b"SECRET"),
        (b"snmp-server community 12345 RO", b"12345"),
        (b"crypto isakmp key 12345 address 0.0.0.0", b"12345"),
        (b"crypto isakmp key exchange-2024 address 10.0.0.1", b"exchange-2024"),
        (b"crypto isakmp key CHAIN.99 address 10.0.0.1", b"CHAIN.99"),
        (b"snmp-server user U G v3 auth md5 AUTHPASS priv des56 PRIVPASS", b"AUTHPASS"),
        (b"snmp-server user U G v3 auth md5 AUTHPASS priv des56 PRIVPASS", b"PRIVPASS"),
        (b"snmp-server user U G v3 priv des56 PRIVPASS", b"PRIVPASS"),
        (b"key 1", b"1"),
        (b"tunnel key 100", b"100"),
    )

    MUST_KEEP = (
        b"crypto key generate rsa modulus 2048",
        b"key chain MYCHAIN",
        b"ppp authentication chap",
        b"Press any key to continue",
        b"Youngest key id is 1",
    )


class ConsoleCleanWorkData:
    """Counts bytes ConsoleReconstructor hands to _clean."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from src import console_reconstruct

        self.total = 0
        original = console_reconstruct._clean

        def counting_clean(line: bytes) -> str:
            self.total += len(line)
            return original(line)

        monkeypatch.setattr(console_reconstruct, "_clean", counting_clean)


class ConsoleBlockingWriterData:
    """Fake _write; first batch blocks, later ones record."""

    def __init__(self) -> None:
        self.entered = asyncio.Event()
        self.written: list = []
        self._blocked = False

    async def __call__(self, batch: list) -> None:
        if not self._blocked:
            self._blocked = True
            self.entered.set()
            await asyncio.Event().wait()
        self.written.extend(batch)


class ConsoleCommitGateData:
    """Fake session factory whose chosen commit blocks forever."""

    def __init__(self, block_commit: int) -> None:
        self._block_commit = block_commit
        self._staged: list = []
        self.commits = 0
        self.reached = asyncio.Event()
        self.rows: list = []

    def __call__(self) -> "ConsoleCommitGateData":
        return self

    async def __aenter__(self) -> "ConsoleCommitGateData":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    def add_all(self, rows: list) -> None:
        self._staged = list(rows)

    async def commit(self) -> None:
        self.commits += 1
        if self.commits == self._block_commit:
            self.reached.set()
            await asyncio.Event().wait()
        self.rows.extend(self._staged)

    def count(self, model) -> int:
        """How many rows of one table were committed."""
        return len([row for row in self.rows if isinstance(row, model)])


class ConsoleWriteBatchData:
    """One chunk frame and one command record."""

    TS = datetime(2026, 1, 1, tzinfo=UTC)

    @staticmethod
    def submit(capture: ConsoleCapture) -> None:
        """Queues one of each kind onto the capture."""
        session_id = uuid.uuid4()
        connection_id = uuid.uuid4()
        capture.submit(
            ConsoleFrame(
                session_id=session_id,
                node_id="node-1",
                connection_id=connection_id,
                seq=1,
                direction="out",
                payload=b"line one\r\n",
                truncated=False,
                redacted=False,
                ts=ConsoleWriteBatchData.TS,
            )
        )
        capture.submit(
            ConsoleCommandRecord(
                session_id=session_id,
                node_id="node-1",
                connection_id=connection_id,
                seq=1,
                prompt="R1#",
                command="show version",
                response="ok",
                ts=ConsoleWriteBatchData.TS,
                duration_ms=1.0,
            )
        )


class ConsoleStalledLookupData:
    """A console socket whose session lookup never answers."""

    @staticmethod
    def build(monkeypatch: pytest.MonkeyPatch, timeout_sec: float):
        """A fake WebSocket carrying a capture, with _resolve_session hung."""

        async def never_answers(app, project_id):
            await asyncio.Event().wait()

        monkeypatch.setattr("src.routers.console_ws._resolve_session", never_answers)
        monkeypatch.setattr("src.routers.console_ws._SESSION_LOOKUP_TIMEOUT_SEC", timeout_sec)
        capture = ConsoleCapture(db_factory=None)
        app = SimpleNamespace(state=SimpleNamespace(console_capture=capture))
        return SimpleNamespace(app=app)


class MigrationOpRecorderData:
    """Stands in for alembic's `op` inside a migration module."""

    def __init__(self) -> None:
        self.created: list[dict] = []
        self.dropped: list[dict] = []
        self.calls: list[tuple[str, str]] = []

    def get_context(self) -> "MigrationOpRecorderData":
        return self

    @contextmanager
    def autocommit_block(self):
        yield

    def create_index(self, index_name, table_name, columns, **kwargs) -> None:
        self.created.append({"name": index_name, **kwargs})
        self.calls.append(("create", index_name))

    def drop_index(self, index_name, **kwargs) -> None:
        self.dropped.append({"name": index_name, **kwargs})
        self.calls.append(("drop", index_name))


class ConsoleIndexMigrationData:
    """Loads the console index migration with a recording `op`."""

    PATH = (
        Path(__file__).resolve().parents[3]
        / "alembic"
        / "versions"
        / "f1a2b3c4d5e6_console_project_index.py"
    )

    @staticmethod
    def load(recorder: MigrationOpRecorderData):
        """The migration module, wired to the recorder."""
        spec = importlib.util.spec_from_file_location(
            "console_project_index_migration", ConsoleIndexMigrationData.PATH
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.op = recorder
        return module
