"""POST /chat/stream — SSE стриминг тьютора (Vercel AI SDK v1)."""

import json
import logging
import uuid
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from chat.persistence import save_assistant_message, save_user_message, to_openai_messages
from chat.schemas import ChatStreamRequest
from chat.stream_protocol import (
    done_event, error_event, finish_event, start_event,
    text_delta, text_end, text_start,
    tool_input_available, tool_input_delta, tool_input_start, tool_output_available,
)
from chat.tools import TOOL_DEFINITIONS, execute_tool
from db.session import get_db
from deps import get_mcp_client
from llm.client import default_model, get_llm_client
from llm.prompts import LANGUAGE_REMINDER, TUTOR_SYSTEM_PROMPT
from sessions.context import build_session_context
from sessions.service import get_owned_session

logger = logging.getLogger(__name__)
router = APIRouter()
# Максимум раундов tool-вызовов в одном /chat ответе, защита от бесконечной рекурсии.
MAX_TOOL_ROUNDS = 5


async def _stream_one_round(
    request: Request,
    client,
    model: str,
    messages: list[dict],
    ctx,
    mcp_client,
    state: dict,
) -> AsyncIterator[str]:
    """Один LLM-round: текст + накопление tool_calls. Обновляет state in-place.

    state keys:
      - assistant_parts: list[dict] — собранные text-парты
      - usage_info: dict | None
      - has_tool_calls: bool — есть ли tool_calls в этом раунде
    """
    stream = await client.chat.completions.create(
        model=model, messages=messages,
        tools=TOOL_DEFINITIONS, tool_choice="auto", stream=True,
    )
    text_buffer: list[str] = []
    text_part_id = None
    tool_calls_buffer: dict[int, dict] = {}
    has_tool_calls = False

    async for chunk in stream:
        if await request.is_disconnected():
            await stream.close()
            raise GeneratorExit
        delta = chunk.choices[0].delta if chunk.choices else None
        if getattr(chunk, "usage", None):
            state["usage_info"] = (
                chunk.usage.model_dump() if hasattr(chunk.usage, "model_dump") else dict(chunk.usage)
            )
        if delta is None:
            continue
        if delta.content:
            if text_part_id is None:
                text_part_id = str(uuid.uuid4())
                yield text_start(text_part_id)
            yield text_delta(text_part_id, delta.content)
            text_buffer.append(delta.content)
        if delta.tool_calls:
            has_tool_calls = True
            for tc in delta.tool_calls:
                idx = tc.index
                buf = tool_calls_buffer.setdefault(idx, {"id": "", "name": "", "arguments": ""})
                if tc.id:
                    buf["id"] = tc.id
                if tc.function:
                    if tc.function.name:
                        buf["name"] = tc.function.name
                    if tc.function.arguments:
                        buf["arguments"] += tc.function.arguments

    if text_part_id is not None:
        yield text_end(text_part_id)
        full = "".join(text_buffer)
        if full:
            state["assistant_parts"].append({"type": "text", "text": full})

    state["has_tool_calls"] = has_tool_calls and bool(tool_calls_buffer)
    if not state["has_tool_calls"]:
        return

    assistant_tool_calls = [
        {"id": tc["id"], "type": "function", "function": {"name": tc["name"], "arguments": tc["arguments"]}}
        for _, tc in sorted(tool_calls_buffer.items())
    ]
    messages.append({"role": "assistant", "content": None, "tool_calls": assistant_tool_calls})

    for tcc in assistant_tool_calls:
        tc_id, tc_name, raw = tcc["id"], tcc["function"]["name"], tcc["function"]["arguments"]
        yield tool_input_start(tc_id, tc_name)
        if raw:
            yield tool_input_delta(tc_id, raw)
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {}
        yield tool_input_available(tc_id, tc_name, parsed)
        result = await execute_tool(tc_name, parsed, ctx, mcp_client)
        yield tool_output_available(tc_id, result)
        messages.append({"role": "tool", "tool_call_id": tc_id, "content": f"{result}\n\n[{LANGUAGE_REMINDER}]"})


async def _finalize_assistant_message(
    db: AsyncSession, session_id: str, parts: list[dict], usage: dict | None
) -> None:
    """Сохранить итоговое сообщение ассистента; ошибки логируем, не пробрасываем (finally-блок)."""
    try:
        await save_assistant_message(db, session_id, parts, usage)
    except Exception:
        logger.exception("chat: не удалось сохранить assistant message session_id=%s", session_id)


@router.post("/chat/stream")
async def chat_stream(
    body: ChatStreamRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    mcp_client=Depends(get_mcp_client),
):
    """Стримит ответ тьютора по сессии через SSE с поддержкой tool-вызовов."""
    session = await get_owned_session(db, body.id, current_user["id"])
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    ctx = build_session_context(session)

    openai_messages = to_openai_messages(body.messages)
    if not openai_messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    await save_user_message(db, session.id, body.messages)

    async def generate():
        """Генератор SSE-событий. Прогоняет раунды LLM и сохраняет итог ассистента."""
        client = get_llm_client()
        model = default_model()
        messages = [{"role": "system", "content": TUTOR_SYSTEM_PROMPT}, *openai_messages]
        message_id = str(uuid.uuid4())
        yield start_event(message_id)

        state: dict = {"assistant_parts": [], "usage_info": None, "has_tool_calls": False}
        tool_round = 0
        try:
            while tool_round < MAX_TOOL_ROUNDS:
                if await request.is_disconnected():
                    break
                async for event in _stream_one_round(
                    request, client, model, messages, ctx, mcp_client, state
                ):
                    yield event
                if not state["has_tool_calls"]:
                    break
                tool_round += 1

            yield finish_event()
            yield done_event()
        except (Exception, GeneratorExit) as exc:
            if not isinstance(exc, GeneratorExit):
                yield error_event(str(exc))
                yield done_event()
        finally:
            await _finalize_assistant_message(
                db, session.id, state["assistant_parts"], state["usage_info"]
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"x-vercel-ai-ui-message-stream": "v1", "Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
