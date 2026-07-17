# UI Message Stream protocol v1 для Vercel AI SDK.
# Header: x-vercel-ai-ui-message-stream: v1
# Content-Type: text/event-stream
# Имена полей должны совпадать с Zod strictObject схемами в пакете ai.
import json
import uuid


def sse_event(data: dict | str) -> str:
    """Форматирует данные в SSE-событие `data: ...\n\n`.

    Args:
        data: dict (сериализуется в JSON) или строка.

    Returns:
        SSE-строка.
    """
    if isinstance(data, str):
        return f"data: {data}\n\n"
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def start_event(message_id: str | None = None) -> str:
    """SSE: начало стрима с messageId."""
    return sse_event({"type": "start", "messageId": message_id or str(uuid.uuid4())})


def text_start(part_id: str | None = None) -> str:
    """SSE: начало текстовой части."""
    return sse_event({"type": "text-start", "id": part_id or str(uuid.uuid4())})


def text_delta(part_id: str, delta: str) -> str:
    """SSE: дельта текста для части part_id."""
    return sse_event({"type": "text-delta", "id": part_id, "delta": delta})


def text_end(part_id: str) -> str:
    """SSE: конец текстовой части."""
    return sse_event({"type": "text-end", "id": part_id})


def tool_input_start(tool_call_id: str, tool_name: str) -> str:
    """SSE: начало ввода инструмента."""
    return sse_event(
        {"type": "tool-input-start", "toolCallId": tool_call_id, "toolName": tool_name}
    )


def tool_input_delta(tool_call_id: str, delta: str) -> str:
    """SSE: дельта аргументов инструмента."""
    return sse_event(
        {"type": "tool-input-delta", "toolCallId": tool_call_id, "inputTextDelta": delta}
    )


def tool_input_available(tool_call_id: str, tool_name: str, input_data: dict) -> str:
    """SSE: полные аргументы инструмента готовы."""
    return sse_event(
        {
            "type": "tool-input-available",
            "toolCallId": tool_call_id,
            "toolName": tool_name,
            "input": input_data,
        }
    )


def tool_output_available(tool_call_id: str, output: str) -> str:
    """SSE: результат выполнения инструмента."""
    return sse_event(
        {"type": "tool-output-available", "toolCallId": tool_call_id, "output": output}
    )


def finish_event() -> str:
    """SSE: завершение стрима."""
    return sse_event({"type": "finish"})


def done_event() -> str:
    """SSE: сигнал [DONE]."""
    return sse_event("[DONE]")


def error_event(message: str) -> str:
    """SSE: событие ошибки."""
    return sse_event({"type": "error", "errorText": message})
