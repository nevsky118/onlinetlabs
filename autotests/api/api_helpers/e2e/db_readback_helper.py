# Tier 2. Reading the written rows directly from the DB (backend-venv).

import os

from sqlalchemy import select

from autotests.settings.configuration.env_paths import env_file

# db/session.py reads settings at module level, so env must be loaded before the import.
_BACKEND_ENV = env_file("backend")
if _BACKEND_ENV.exists():
    from dotenv import dotenv_values
    for _k, _v in dotenv_values(str(_BACKEND_ENV)).items():
        os.environ.setdefault(_k, _v)


async def fetch_chat_messages(session_id: str) -> list:
    """Return the chat_messages for a session (in-process, backend async_session)."""
    from db.session import async_session
    from models.chat_message import ChatMessage
    async with async_session() as db:
        result = await db.execute(
            select(ChatMessage).where(ChatMessage.session_id == session_id)
        )
        return list(result.scalars().all())
