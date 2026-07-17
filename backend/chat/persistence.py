"""Persists chat messages to chat_messages."""

from sqlalchemy import select

from models.chat_message import ChatMessage


def to_openai_messages(sdk_messages: list[dict]) -> list[dict]:
    """Converts SDK messages to OpenAI format with role and text content."""
    converted: list[dict] = []
    for msg in sdk_messages:
        role = msg.get("role", "user")
        parts = msg.get("parts")
        if parts and isinstance(parts, list):
            pieces = [p["text"] for p in parts if p.get("type") == "text" and p.get("text")]
            content = "\n".join(pieces)
        else:
            content = msg.get("content", "")
        if content:
            converted.append({"role": role, "content": content})
    return converted


async def save_user_message(db, session_id: str, sdk_messages: list[dict]) -> None:
    """Saves the last user message from the list to the database."""
    last = sdk_messages[-1] if sdk_messages else None
    if not last or last.get("role") != "user":
        return
    parts = last.get("parts") or [{"type": "text", "text": last.get("content", "")}]
    db.add(ChatMessage(session_id=session_id, role="user", parts=parts))
    await db.commit()


async def save_assistant_message(
    db, session_id: str, parts: list[dict], usage: dict | None
) -> None:
    """Saves the assistant message with its parts and token usage."""
    if not parts:
        return
    db.add(ChatMessage(session_id=session_id, role="assistant", parts=parts, usage=usage))
    await db.commit()


async def get_chat_history(db, session_id: str) -> list["ChatMessage"]:
    """Returns all session messages ordered by creation time ascending."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return list(result.scalars().all())
