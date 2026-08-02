"""SSE tutor streaming for POST /chat/stream (Vercel AI SDK v1)."""

import asyncio
import json
import logging
import re
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from agents._shared import language_directive
from auth.dependencies import get_current_user, require_active_user
from chat.persistence import save_assistant_message, save_user_message, to_openai_messages
from chat.prompt import build_system_content
from chat.schemas import ChatStreamRequest
from chat.stream_protocol import (
    done_event,
    error_event,
    finish_event,
    start_event,
    text_delta,
    text_end,
    text_start,
    tool_input_available,
    tool_input_delta,
    tool_input_start,
    tool_output_available,
)
from chat.tools import TOOL_DEFINITIONS, execute_tool, run_vpcs_show_ip
from config import settings
from core.llm.client import build_client, model_supports_tools, model_uri
from db.session import get_db
from deps import get_locale, get_mcp_client
from i18n import Locale, LocalizedError, resolve_localized, t
from labs.spec import expected_vpcs_config
from models.lab import Lab
from models.user import User
from observability.models import (
    event_fallback,
    event_mcp_context_fetched,
    event_model_selected,
    event_response_finished,
    event_tool_call,
    event_tool_result,
)
from sessions.context import build_session_context
from sessions.service import get_owned_session
from validation.runner import load_lab_spec

logger = logging.getLogger(__name__)
router = APIRouter()


def _activity_emit(app_state, event) -> None:
    """Safely emits an activity event if the log service is available."""
    log = getattr(app_state, "activity_log", None)
    if log is not None:
        log.emit(event)


# Max tool-call rounds in a single /chat response, guards against infinite recursion.
MAX_TOOL_ROUNDS = 5

# Recent dialogue messages sent to the model. The [TASK] and [LAB_STATE] prompt
# sections are rebuilt every request, so older turns add no context and repeat
# stale claims about the environment.
MAX_HISTORY_MESSAGES = 6

# Regex for stripping YandexGPT thinking tokens from streamed content.
_THINKING_RE = re.compile(r"\[START_THINKING\].*?\[END_THINKING\]", re.DOTALL)


def build_models_response(can_select: bool, user_default_model_id: str | None = None) -> dict:
    """Model catalog for the UI, filtered to tools-capable entries only; empty if selection is disallowed.

    `default_model_id` reports what the next message will use: user preference over config.
    """
    cfg = settings.agents
    models = (
        [] if not can_select else [{"id": m.id, "label": m.label} for m in cfg.catalog if m.tools]
    )
    default_model_id = cfg.chat_model
    if can_select and user_default_model_id and cfg.get_entry(user_default_model_id) is not None:
        default_model_id = user_default_model_id
    return {"can_select": can_select, "default_model_id": default_model_id, "models": models}


@router.get("/chat/models")
async def chat_models(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Models available for selection to the current user."""
    user = await db.get(User, current_user["id"])
    return build_models_response(
        current_user.get("can_select", False),
        user_default_model_id=user.default_model_id if user else None,
    )


def resolve_chat_model(
    requested: str | None,
    session_model_id: str | None,
    can_select: bool,
    user_default_model_id: str | None = None,
) -> str:
    """Resolves which model to use.

    Precedence: request > user preference > session model > config default.
    The first two require can_select, matching how the preference is written.
    """
    cfg = settings.agents
    if can_select and requested and cfg.get_entry(requested) is not None:
        return requested
    if can_select and user_default_model_id and cfg.get_entry(user_default_model_id) is not None:
        return user_default_model_id
    if session_model_id and cfg.get_entry(session_model_id) is not None:
        return session_model_id
    return cfg.chat_model


def _supports_tool_calling(model_id: str) -> bool:
    """Whether the model supports native OpenAI-style function calling."""
    return model_supports_tools(model_id)


async def _fetch_mcp_context(
    mcp_client, ctx, locale: Locale, expected_vpcs: dict | None = None
) -> tuple[str | None, int, int]:
    """Preloads environment state from MCP as text plus structural component and error counts.

    Runs before the first LLM round so models without tool-calling (YandexGPT) still get real state.

    expected_vpcs: node_name -> {"ip", "gateway"} from the [TASK] prompt section. Used to label each
    actual IP correct/incorrect here rather than asking the model to compare.
    """
    expected_vpcs = expected_vpcs or {}
    if mcp_client is None:
        return None, 0, 0
    try:
        components, errors = await asyncio.gather(
            mcp_client.list_components(ctx),
            mcp_client.list_errors(ctx),
            return_exceptions=True,
        )
        parts = []
        component_count = 0
        error_count = 0
        if isinstance(components, list) and components:
            component_count = len(components)
            lines = [f"  - {c.name} ({c.type}): {c.status} — {c.summary}" for c in components]
            parts.append(t("prompt.env.components", locale) + "\n" + "\n".join(lines))

            # Run show ip ourselves: models often skip get_vpcs_ip and echo the
            # expected values from [TASK] instead.
            vpcs_nodes = [c for c in components if c.type == "vpcs" and c.status == "started"]
            if vpcs_nodes:
                ip_results = await asyncio.gather(
                    *(run_vpcs_show_ip(c.name, ctx, mcp_client, locale) for c in vpcs_nodes),
                    return_exceptions=True,
                )
                lines = []
                for c, res in zip(vpcs_nodes, ip_results):
                    if isinstance(res, Exception) or "error" in res:
                        continue
                    actual_ip = res.get("ip")
                    gw = res.get("gateway", "")
                    line = f"  - {c.name}: IP={actual_ip or t('prompt.env.ip_unset', locale)}"
                    if gw and gw != "0.0.0.0":
                        line += f", gateway={gw}"
                    expected = expected_vpcs.get(c.name)
                    if expected and expected.get("ip"):
                        if actual_ip == expected["ip"]:
                            line += t("prompt.env.verdict_ok", locale)
                        else:
                            line += t("prompt.env.verdict_bad", locale, expected=expected["ip"])
                    lines.append(line)
                if lines:
                    parts.append(t("prompt.env.vpcs_current", locale) + "\n" + "\n".join(lines))
        else:
            parts.append(t("prompt.env.components_empty", locale))

        if isinstance(errors, list):
            recent = [e for e in errors if not isinstance(e, Exception)][:5]
            error_count = len(recent)
            if recent:
                lines = [
                    f"  - [{e.level.value}] {e.component_id or '?'}: {e.message}" for e in recent
                ]
                parts.append(t("prompt.env.recent_errors", locale) + "\n" + "\n".join(lines))
            else:
                parts.append(t("prompt.env.no_errors", locale))
        return ("\n\n".join(parts) if parts else None), component_count, error_count
    except Exception:
        logger.warning("chat: failed to preload the MCP context", exc_info=True)
        return None, 0, 0


async def _fetch_lab_context(
    db: AsyncSession, lab_slug: str, spec: dict | None, locale: Locale
) -> str | None:
    """Loads the lab description and expected configuration from the DB and YAML spec."""
    try:
        lab = await db.get(Lab, lab_slug)
        if lab is None:
            return None
        parts = [t("prompt.lab.title", locale, title=resolve_localized(lab.title_i18n, locale))]
        description = resolve_localized(lab.description_i18n, locale)
        if description:
            parts.append(t("prompt.lab.goal", locale, goal=description))

        if spec is not None:
            steps = spec.get("steps", [])
            if steps:
                step_lines = []
                for step in steps:
                    title = resolve_localized(step.get("title", step.get("id", "?")), locale)
                    step_lines.append(t("prompt.lab.step", locale, title=title))
                    for check in step.get("checks", []):
                        kind = check.get("kind", "")
                        expect = check.get("expect", {})
                        if kind == "vpcs.show_ip":
                            line = t(
                                "prompt.lab.check_show_ip",
                                locale,
                                node=check.get("node", "?"),
                                ip=expect.get("ip", "?"),
                            )
                            gw = expect.get("gateway", "")
                            if gw and gw != "0.0.0.0":
                                line += t("prompt.lab.check_gateway", locale, gateway=gw)
                            step_lines.append(line)
                        elif kind == "vpcs.ping":
                            step_lines.append(
                                t(
                                    "prompt.lab.check_ping",
                                    locale,
                                    source=check.get("from", "?"),
                                    target=check.get("to", "?"),
                                )
                            )
                        elif kind == "vpcs.ip_in_subnet":
                            step_lines.append(
                                t(
                                    "prompt.lab.check_subnet",
                                    locale,
                                    node=check.get("node", "?"),
                                    subnet=expect.get("subnet", "?"),
                                )
                            )
                parts.append(t("prompt.lab.steps_header", locale) + "\n" + "\n".join(step_lines))

        return "\n".join(parts)
    except Exception:
        logger.warning("chat: failed to load the lab context %s", lab_slug, exc_info=True)
        return None


async def _stream_one_round(
    request: Request,
    client,
    model: str,
    messages: list[dict],
    ctx,
    mcp_client,
    state: dict,
    locale: Locale,
    model_id: str = "",
    app_state=None,
    session_id: str = "",
    user_id: str = "",
) -> AsyncIterator[str]:
    """Runs one LLM round, accumulating text and tool_calls; updates state in-place.

    state keys:
      - assistant_parts (list[dict]): collected text parts
      - usage_info (dict | None)
      - has_tool_calls (bool): whether this round has tool_calls
    """
    cfg = settings.agents
    create_kwargs: dict = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
    }
    if _supports_tool_calling(model_id):
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
                chunk.usage.model_dump()
                if hasattr(chunk.usage, "model_dump")
                else dict(chunk.usage)
            )
        if delta is None:
            continue
        if delta.content:
            # Strip YandexGPT thinking tokens before passing into the stream.
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
        {
            "id": tc["id"],
            "type": "function",
            "function": {"name": tc["name"], "arguments": tc["arguments"]},
        }
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
        _activity_emit(
            app_state,
            event_tool_call(
                session_id,
                user_id,
                name=tc_name,
                args_preview=str(parsed)[:200],
            ),
        )
        result = await execute_tool(tc_name, parsed, ctx, mcp_client, locale)
        _activity_emit(
            app_state,
            event_tool_result(
                session_id,
                user_id,
                name=tc_name,
                result_preview=str(result)[:200],
                success="error" not in str(result).lower(),
            ),
        )
        yield tool_output_available(tc_id, result)
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tc_id,
                "content": f"{result}\n\n[{language_directive(locale)}]",
            }
        )


async def _finalize_assistant_message(
    db: AsyncSession, session_id: str, parts: list[dict], usage: dict | None, model_id: str
) -> None:
    """Save the final assistant message; log errors, don't propagate (finally block)."""
    try:
        merged = {**(usage or {}), "model_id": model_id}
        await save_assistant_message(db, session_id, parts, merged)
    except Exception:
        logger.exception("chat: failed to save the assistant message session_id=%s", session_id)


@router.post("/chat/stream")
async def chat_stream(
    body: ChatStreamRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    _active: dict = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
    mcp_client=Depends(get_mcp_client),
    locale: Locale = Depends(get_locale),
):
    """Streams the tutor's response for a session via SSE with tool-call support."""
    session = await get_owned_session(db, body.id, current_user["id"])
    if session is None:
        raise LocalizedError("error.session.not_found", status_code=404)
    ctx = build_session_context(session)

    openai_messages = to_openai_messages(body.messages)
    if not openai_messages:
        raise LocalizedError("error.chat.no_messages", status_code=400)
    await save_user_message(db, session.id, body.messages)

    # Read before the generator starts: the request-scoped session is gone by the
    # time the SSE body streams.
    user_row = await db.get(User, current_user["id"])
    user_default_model_id = user_row.default_model_id if user_row else None

    async def generate():
        """SSE event generator. Runs LLM rounds and saves the assistant's final message."""
        effective_model_id = resolve_chat_model(
            body.model_id,
            session.model_id,
            current_user.get("can_select", False),
            user_default_model_id=user_default_model_id,
        )
        if body.model_id and effective_model_id != body.model_id:
            logger.warning(
                "chat: model_id '%s' rejected, fallback to '%s'", body.model_id, effective_model_id
            )
            _activity_emit(
                request.app.state,
                event_fallback(
                    session.id,
                    current_user["id"],
                    original_model=body.model_id,
                    fallback_model=effective_model_id,
                    reason="not in catalog or selection not permitted",
                ),
            )
        # Persist the model choice to the session.
        if effective_model_id != session.model_id:
            session.model_id = effective_model_id
            await db.commit()
        client = build_client(effective_model_id)
        model = model_uri(effective_model_id)
        entry = settings.agents.get_entry(effective_model_id)
        _activity_emit(
            request.app.state,
            event_model_selected(
                session.id,
                current_user["id"],
                model_id=effective_model_id,
                provider=entry.provider_ref if entry else "unknown",
            ),
        )

        # Loads lab description and environment state from MCP in parallel.
        spec = load_lab_spec(session.lab_slug)
        expected_vpcs = expected_vpcs_config(spec)
        lab_ctx_text, mcp_result = await asyncio.gather(
            _fetch_lab_context(db, session.lab_slug, spec, locale),
            _fetch_mcp_context(mcp_client, ctx, locale, expected_vpcs),
        )
        mcp_ctx_text, component_count, error_count = mcp_result
        _activity_emit(
            request.app.state,
            event_mcp_context_fetched(
                session.id,
                current_user["id"],
                component_count=component_count,
                error_count=error_count,
                verdict_summary=("ok" if mcp_ctx_text else "no_context"),
            ),
        )
        system_content = build_system_content(locale, lab_ctx_text, mcp_ctx_text)

        messages = [
            {"role": "system", "content": system_content},
            *openai_messages[-MAX_HISTORY_MESSAGES:],
        ]
        message_id = str(uuid.uuid4())
        yield start_event(message_id)

        state: dict = {"assistant_parts": [], "usage_info": None, "has_tool_calls": False}
        tool_round = 0
        try:
            while tool_round < MAX_TOOL_ROUNDS:
                if await request.is_disconnected():
                    break
                async for event in _stream_one_round(
                    request,
                    client,
                    model,
                    messages,
                    ctx,
                    mcp_client,
                    state,
                    locale,
                    model_id=effective_model_id,
                    app_state=request.app.state,
                    session_id=session.id,
                    user_id=current_user["id"],
                ):
                    yield event
                if not state["has_tool_calls"]:
                    break
                tool_round += 1

            usage = state.get("usage_info") or {}
            _activity_emit(
                request.app.state,
                event_response_finished(
                    session.id,
                    current_user["id"],
                    model_id=effective_model_id,
                    total_tokens=usage.get("total_tokens", 0),
                    stop_reason="stop",
                ),
            )
            yield finish_event()
            yield done_event()
        except (Exception, GeneratorExit) as exc:
            if not isinstance(exc, GeneratorExit):
                yield error_event(str(exc))
                yield done_event()
        finally:
            await _finalize_assistant_message(
                db, session.id, state["assistant_parts"], state["usage_info"], effective_model_id
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "x-vercel-ai-ui-message-stream": "v1",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
