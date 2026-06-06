# Tier 2: чтение записанных строк напрямую из БД (backend-venv).

import os
from pathlib import Path

from sqlalchemy import select

# db/session.py читает settings на уровне модуля — нужно загрузить env до импорта.
_LOCAL_ENV = Path(__file__).parents[4] / "backend" / ".env"
if _LOCAL_ENV.exists():
    from dotenv import dotenv_values
    for _k, _v in dotenv_values(str(_LOCAL_ENV)).items():
        os.environ.setdefault(_k, _v)


async def fetch_chat_messages(session_id: str) -> list:
    """Вернуть chat_messages для сессии (in-process, backend async_session)."""
    from db.session import async_session
    from models.chat_message import ChatMessage
    async with async_session() as db:
        result = await db.execute(
            select(ChatMessage).where(ChatMessage.session_id == session_id)
        )
        return list(result.scalars().all())
