"""Unit tests for chat/persistence.py."""

from datetime import UTC, datetime, timedelta

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from chat.persistence import (
    get_chat_history,
    save_assistant_message,
    save_user_message,
    to_openai_messages,
)
from models.chat_message import ChatMessage

pytestmark = [pytest.mark.unit]


class TestToOpenAIMessages:
    """Pure (sync) function converting sdk messages to openai format."""

    @autotest.num("1910")
    @autotest.external_id("c1f25a02-2f6a-4f70-9ad9-3ab9f4a01a30")
    @autotest.name("to_openai_messages: multi-part user → joins text parts with \\n")
    def test_c1f25a02_joins_multipart_text(self):
        with autotest.step("Prepare a message with two text parts"):
            sdk_messages = [
                {
                    "role": "user",
                    "parts": [
                        {"type": "text", "text": "hello"},
                        {"type": "text", "text": "world"},
                    ],
                }
            ]

        with autotest.step("Convert"):
            result = to_openai_messages(sdk_messages)

        with autotest.step("Texts joined with \\n, role preserved"):
            assert_equal(len(result), 1, "len(result)")
            assert_equal(result[0]["role"], "user", "role")
            assert_equal(result[0]["content"], "hello\nworld", "content")

    @autotest.num("1911")
    @autotest.external_id("4cc1c0db-49f8-4f23-9d80-1d65bb0a3c7c")
    @autotest.name("to_openai_messages: content only (no parts) → takes content")
    def test_4cc1c0db_uses_content_when_no_parts(self):
        with autotest.step("Prepare a message without parts"):
            sdk_messages = [{"role": "assistant", "content": "plain answer"}]

        with autotest.step("Convert"):
            result = to_openai_messages(sdk_messages)

        with autotest.step("Takes content"):
            assert_equal(len(result), 1, "len(result)")
            assert_equal(result[0]["content"], "plain answer", "content")
            assert_equal(result[0]["role"], "assistant", "role")

    @autotest.num("1912")
    @autotest.external_id("3a9d6a72-2b8a-4a82-b89f-bf3a4d3b5b3c")
    @autotest.name("to_openai_messages: empty parts → skipped")
    def test_3a9d6a72_skips_empty_parts(self):
        with autotest.step("Message with empty text parts"):
            sdk_messages = [
                {"role": "user", "parts": [{"type": "text", "text": ""}]},
                {"role": "user", "parts": []},
                {"role": "user", "content": "kept"},
            ]

        with autotest.step("Convert"):
            result = to_openai_messages(sdk_messages)

        with autotest.step("Only non-empty messages make it into the result"):
            assert_equal(len(result), 1, "len(result)")
            assert_equal(result[0]["content"], "kept", "content")

    @autotest.num("1913")
    @autotest.external_id("88c1bb5d-2c7b-4c80-8c4e-2e6f8f5d2d11")
    @autotest.name("to_openai_messages: non-text parts → ignored")
    def test_88c1bb5d_ignores_non_text_parts(self):
        with autotest.step("Message with image+text"):
            sdk_messages = [
                {
                    "role": "user",
                    "parts": [
                        {"type": "image", "url": "http://x/y.png"},
                        {"type": "text", "text": "describe"},
                    ],
                }
            ]

        with autotest.step("Convert"):
            result = to_openai_messages(sdk_messages)

        with autotest.step("Only the text part ends up in content"):
            assert_equal(len(result), 1, "len(result)")
            assert_equal(result[0]["content"], "describe", "content")


class _DBTestBase:
    """Shared in-memory SQLite setup for just the chat_messages table."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        # We don't need the FK on learning_sessions, SQLite doesn't
        # enforce FKs by default, and we leave it that way.
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(ChatMessage.__table__.create)
        yield
        await self.engine.dispose()


class TestSaveUserMessage(_DBTestBase):
    @autotest.num("1914")
    @autotest.external_id("a7b1f8d3-8d2e-4c91-9b7e-2f4a6c1d8e0a")
    @autotest.name("save_user_message: last message is user → INSERT with the same parts")
    async def test_a7b1f8d3_inserts_user_row(self):
        with autotest.step("Prepare sdk_messages ending in a user message"):
            parts = [{"type": "text", "text": "hi"}]
            sdk_messages = [
                {"role": "assistant", "content": "previous"},
                {"role": "user", "parts": parts},
            ]

        with autotest.step("Save"):
            async with self.session_factory() as db:
                await save_user_message(db, "sess-1", sdk_messages)

        with autotest.step("DB has exactly one user row with the same parts"):
            async with self.session_factory() as db:
                rows = await get_chat_history(db, "sess-1")
            assert_equal(len(rows), 1, "rows count")
            assert_equal(rows[0].role, "user", "role")
            assert_equal(rows[0].session_id, "sess-1", "session_id")
            assert_equal(rows[0].parts, parts, "parts")

    @autotest.num("1915")
    @autotest.external_id("d2e8b1c4-9f3a-4b88-8d12-5b9c0e2f1a33")
    @autotest.name("save_user_message: last message is assistant → not saved")
    async def test_d2e8b1c4_skips_when_last_is_assistant(self):
        with autotest.step("Last message is from assistant"):
            sdk_messages = [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "answer"},
            ]

        with autotest.step("Save"):
            async with self.session_factory() as db:
                await save_user_message(db, "sess-2", sdk_messages)

        with autotest.step("DB is empty"):
            async with self.session_factory() as db:
                rows = await get_chat_history(db, "sess-2")
            assert_equal(len(rows), 0, "rows count")

    @autotest.num("1916")
    @autotest.external_id("8f4c3a91-7b2d-4e6f-9c01-3a8b5d7e9f12")
    @autotest.name("save_user_message: empty list → no-op")
    async def test_8f4c3a91_skips_when_empty(self):
        with autotest.step("Save an empty list"):
            async with self.session_factory() as db:
                await save_user_message(db, "sess-3", [])

        with autotest.step("DB is empty"):
            async with self.session_factory() as db:
                rows = await get_chat_history(db, "sess-3")
            assert_equal(len(rows), 0, "rows count")


class TestSaveAssistantMessage(_DBTestBase):
    @autotest.num("1917")
    @autotest.external_id("e6c2a489-4d72-49f3-b2c8-1f0e7d4b8a5c")
    @autotest.name("save_assistant_message: parts + usage → INSERT")
    async def test_e6c2a489_inserts_assistant_row_with_usage(self):
        with autotest.step("Prepare parts and usage"):
            parts = [{"type": "text", "text": "answer"}]
            usage = {"prompt_tokens": 10, "completion_tokens": 5}

        with autotest.step("Save"):
            async with self.session_factory() as db:
                await save_assistant_message(db, "sess-a", parts, usage)

        with autotest.step("DB has an assistant row with parts+usage"):
            async with self.session_factory() as db:
                rows = await get_chat_history(db, "sess-a")
            assert_equal(len(rows), 1, "rows count")
            assert_equal(rows[0].role, "assistant", "role")
            assert_equal(rows[0].parts, parts, "parts")
            assert_equal(rows[0].usage, usage, "usage")

    @autotest.num("1918")
    @autotest.external_id("9a1d7e34-3b8c-4f5a-b6d2-8e0f1c2a3b4d")
    @autotest.name("save_assistant_message: empty parts → no-op")
    async def test_9a1d7e34_skips_when_empty_parts(self):
        with autotest.step("Save with empty parts"):
            async with self.session_factory() as db:
                await save_assistant_message(db, "sess-b", [], {"x": 1})

        with autotest.step("DB is empty"):
            async with self.session_factory() as db:
                rows = await get_chat_history(db, "sess-b")
            assert_equal(len(rows), 0, "rows count")


class TestGetChatHistory(_DBTestBase):
    @autotest.num("1919")
    @autotest.external_id("28d51ddb-4f25-4777-97a1-864fb4c43682")
    @autotest.name("get_chat_history: ordered by created_at ASC")
    async def test_28d51ddb_orders_by_created_at_asc(self):
        with autotest.step("Insert 3 messages with explicit created_at in shuffled order"):
            base = datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC)
            async with self.session_factory() as db:
                db.add(
                    ChatMessage(
                        session_id="sess-h",
                        role="user",
                        parts=[{"type": "text", "text": "second"}],
                        created_at=base + timedelta(seconds=10),
                    )
                )
                db.add(
                    ChatMessage(
                        session_id="sess-h",
                        role="assistant",
                        parts=[{"type": "text", "text": "third"}],
                        created_at=base + timedelta(seconds=20),
                    )
                )
                db.add(
                    ChatMessage(
                        session_id="sess-h",
                        role="user",
                        parts=[{"type": "text", "text": "first"}],
                        created_at=base,
                    )
                )
                await db.commit()

        with autotest.step("Read the history"):
            async with self.session_factory() as db:
                rows = await get_chat_history(db, "sess-h")

        with autotest.step("ASC order by created_at"):
            assert_equal(len(rows), 3, "rows count")
            assert_equal(rows[0].parts[0]["text"], "first", "rows[0]")
            assert_equal(rows[1].parts[0]["text"], "second", "rows[1]")
            assert_equal(rows[2].parts[0]["text"], "third", "rows[2]")
            assert_true(
                rows[0].created_at <= rows[1].created_at <= rows[2].created_at,
                "monotonic created_at",
            )
