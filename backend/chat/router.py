"""POST /chat/stream — SSE стриминг тьютора (Vercel AI SDK v1)."""

import asyncio
import json
import logging
import re
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
from chat.tools import TOOL_DEFINITIONS, _run_vpcs_show_ip, execute_tool
from config import settings
from config.config_model import LlmProvider
from db.session import get_db
from deps import get_mcp_client
from llm.client import default_model, get_llm_client
from llm.prompts import LANGUAGE_REMINDER, TUTOR_SYSTEM_PROMPT
from models.lab import Lab
from sessions.context import build_session_context
from sessions.service import get_owned_session

logger = logging.getLogger(__name__)
router = APIRouter()
# Максимум раундов tool-вызовов в одном /chat ответе, защита от бесконечной рекурсии.
MAX_TOOL_ROUNDS = 5

# Сколько последних сообщений диалога отправлять модели. [Задание] и
# [Текущее состояние лаб-среды] пересобираются заново на каждый запрос —
# длинная история не нужна и только усиливает "снежный ком" из повторяющихся
# (возможно неверных) утверждений модели о состоянии среды.
MAX_HISTORY_MESSAGES = 6

# Regex для стриппинга thinking-токенов YandexGPT из стримингового контента.
_THINKING_RE = re.compile(r"\[START_THINKING\].*?\[END_THINKING\]", re.DOTALL)


def _supports_tool_calling() -> bool:
    """Возвращает True для провайдеров с нативным OpenAI-style function calling."""
    return settings.agents.provider in (LlmProvider.ANTHROPIC, LlmProvider.OPENAI, LlmProvider.YANDEX)


async def _fetch_mcp_context(mcp_client, ctx, expected_vpcs: dict | None = None) -> str | None:
    """Предзагружает состояние среды из MCP и форматирует как текстовый блок.

    Вызывается до первого LLM-раунда, чтобы модель получила реальный контекст
    даже если не поддерживает нативный tool-calling (например, YandexGPT).

    expected_vpcs: node_name -> {"ip": ..., "gateway": ...} из [Задание] —
    используется чтобы сразу проставить вердикт «верно/неверно» рядом с
    фактическим IP, не полагаясь на то, что модель сама сравнит значения
    (YandexGPT часто игнорирует это и пересказывает ожидаемые значения).
    """
    expected_vpcs = expected_vpcs or {}
    if mcp_client is None:
        return None
    try:
        components, errors = await asyncio.gather(
            mcp_client.list_components(ctx),
            mcp_client.list_errors(ctx),
            return_exceptions=True,
        )
        parts = []
        if isinstance(components, list):
            if components:
                lines = [f"  - {c.name} ({c.type}): {c.status} — {c.summary}" for c in components]
                parts.append("Компоненты среды:\n" + "\n".join(lines))
            else:
                parts.append("Компоненты среды: список пуст.")

            # Реальный show ip для запущенных VPCS-узлов — не полагаемся на то,
            # что модель сама вызовет get_vpcs_ip (часто она этого не делает
            # и придумывает значения из [Задание]).
            vpcs_nodes = [c for c in components if c.type == "vpcs" and c.status == "started"]
            if vpcs_nodes:
                ip_results = await asyncio.gather(
                    *(_run_vpcs_show_ip(c.name, ctx, mcp_client) for c in vpcs_nodes),
                    return_exceptions=True,
                )
                lines = []
                for c, res in zip(vpcs_nodes, ip_results):
                    if isinstance(res, Exception) or "error" in res:
                        continue
                    actual_ip = res.get("ip")
                    gw = res.get("gateway", "")
                    line = f"  - {c.name}: IP={actual_ip or '(не настроен)'}"
                    if gw and gw != "0.0.0.0":
                        line += f", gateway={gw}"
                    expected = expected_vpcs.get(c.name)
                    if expected and expected.get("ip"):
                        if actual_ip == expected["ip"]:
                            line += " — ВЕРНО (совпадает с заданием)"
                        else:
                            line += f" — ОШИБКА (в задании требуется {expected['ip']})"
                    lines.append(line)
                if lines:
                    parts.append("Текущая конфигурация VPCS (show ip) — снято прямо сейчас:\n" + "\n".join(lines))
        else:
            parts.append("Компоненты среды: список пуст.")

        if isinstance(errors, list):
            recent = [e for e in errors if not isinstance(e, Exception)][:5]
            if recent:
                lines = [f"  - [{e.level.value}] {e.component_id or '?'}: {e.message}" for e in recent]
                parts.append("Последние ошибки:\n" + "\n".join(lines))
            else:
                parts.append("Ошибок не обнаружено.")
        return "\n\n".join(parts) if parts else None
    except Exception:
        logger.warning("chat: не удалось предзагрузить MCP-контекст", exc_info=True)
        return None


def _load_lab_spec(lab_slug: str) -> dict | None:
    """Загружает YAML-спецификацию задания лабы (шаги и ожидаемые значения)."""
    import yaml
    from pathlib import Path

    yaml_path = Path(__file__).parent.parent / "validation" / "labs" / f"{lab_slug}.yaml"
    if not yaml_path.exists():
        return None
    return yaml.safe_load(yaml_path.read_text(encoding="utf-8"))


def _expected_vpcs_config(spec: dict | None) -> dict[str, dict]:
    """Извлекает из спецификации ожидаемый IP/gateway по узлам VPCS: node_name -> {ip, gateway}."""
    result: dict[str, dict] = {}
    if not spec:
        return result
    for step in spec.get("steps", []):
        for check in step.get("checks", []):
            if check.get("kind") == "vpcs.show_ip":
                node = check.get("node")
                if node:
                    expect = check.get("expect", {})
                    result[node] = {"ip": expect.get("ip"), "gateway": expect.get("gateway")}
    return result


async def _fetch_lab_context(db: AsyncSession, lab_slug: str, spec: dict | None) -> str | None:
    """Загружает описание лабы и ожидаемую конфигурацию из БД и YAML-задания."""
    try:
        lab = await db.get(Lab, lab_slug)
        if lab is None:
            return None
        parts = [f"Лабораторная работа: «{lab.title}»"]
        if lab.description:
            parts.append(f"Цель: {lab.description}")

        if spec is not None:
            steps = spec.get("steps", [])
            if steps:
                step_lines = []
                for step in steps:
                    step_lines.append(f"  Шаг «{step.get('title', step.get('id', '?'))}»:")
                    for check in step.get("checks", []):
                        kind = check.get("kind", "")
                        expect = check.get("expect", {})
                        if kind == "vpcs.show_ip":
                            node = check.get("node", "?")
                            ip = expect.get("ip", "?")
                            gw = expect.get("gateway", "")
                            line = f"    - {node}: IP={ip}"
                            if gw and gw != "0.0.0.0":
                                line += f", gateway={gw}"
                            step_lines.append(line)
                        elif kind == "vpcs.ping":
                            frm = check.get("from", "?")
                            to = check.get("to", "?")
                            step_lines.append(f"    - {frm} ping {to}")
                        elif kind == "vpcs.ip_in_subnet":
                            node = check.get("node", "?")
                            subnet = expect.get("subnet", "?")
                            step_lines.append(f"    - {node}: адрес в подсети {subnet}")
                parts.append("Задание (что должен настроить студент):\n" + "\n".join(step_lines))

        return "\n".join(parts)
    except Exception:
        logger.warning("chat: не удалось загрузить контекст лабы %s", lab_slug, exc_info=True)
        return None


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
    create_kwargs: dict = {"model": model, "messages": messages, "stream": True}
    if _supports_tool_calling():
        create_kwargs["tools"] = TOOL_DEFINITIONS
        create_kwargs["tool_choice"] = "auto"

    stream = await client.chat.completions.create(**create_kwargs)
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
            # Стрипаем thinking-токены YandexGPT до передачи в стрим.
            content = _THINKING_RE.sub("", delta.content).strip()
            if not content:
                continue
            if text_part_id is None:
                text_part_id = str(uuid.uuid4())
                yield text_start(text_part_id)
            yield text_delta(text_part_id, content)
            text_buffer.append(content)
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

        # Параллельно загружаем: описание лабы + состояние среды из MCP.
        spec = _load_lab_spec(session.lab_slug)
        expected_vpcs = _expected_vpcs_config(spec)
        lab_ctx_text, mcp_ctx_text = await asyncio.gather(
            _fetch_lab_context(db, session.lab_slug, spec),
            _fetch_mcp_context(mcp_client, ctx, expected_vpcs),
        )
        system_content = TUTOR_SYSTEM_PROMPT
        if lab_ctx_text:
            system_content += f"\n\n[Задание]\n{lab_ctx_text}"
        if mcp_ctx_text:
            system_content += f"\n\n[Текущее состояние лаб-среды]\n{mcp_ctx_text}"

        messages = [{"role": "system", "content": system_content}, *openai_messages[-MAX_HISTORY_MESSAGES:]]
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
