# UI Message Stream protocol v1 for Vercel AI SDK.
# Header: x-vercel-ai-ui-message-stream: v1
# Content-Type: text/event-stream
# Field names must match the Zod strictObject schemas in the ai package.
import json
import uuid


def sse_event(data: dict | str) -> str:
    """Formats data as an SSE event `data: ...\n\n`.

    Args:
        data: dict (serialized to JSON) or a string.

    Returns:
        SSE string.
    """
    if isinstance(data, str):
        return f"data: {data}\n\n"
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def start_event(message_id: str | None = None) -> str:
    """SSE: stream start with messageId."""
    return sse_event({"type": "start", "messageId": message_id or str(uuid.uuid4())})


def text_start(part_id: str | None = None) -> str:
    """SSE: start of a text part."""
    return sse_event({"type": "text-start", "id": part_id or str(uuid.uuid4())})


def text_delta(part_id: str, delta: str) -> str:
    """SSE: text delta for part part_id."""
    return sse_event({"type": "text-delta", "id": part_id, "delta": delta})


def text_end(part_id: str) -> str:
    """SSE: end of a text part."""
    return sse_event({"type": "text-end", "id": part_id})


def tool_input_start(tool_call_id: str, tool_name: str) -> str:
    """SSE: start of tool input."""
    return sse_event(
        {"type": "tool-input-start", "toolCallId": tool_call_id, "toolName": tool_name}
    )


def tool_input_delta(tool_call_id: str, delta: str) -> str:
    """SSE: delta of tool arguments."""
    return sse_event(
        {"type": "tool-input-delta", "toolCallId": tool_call_id, "inputTextDelta": delta}
    )


def tool_input_available(tool_call_id: str, tool_name: str, input_data: dict) -> str:
    """SSE: full tool arguments ready."""
    return sse_event(
        {
            "type": "tool-input-available",
            "toolCallId": tool_call_id,
            "toolName": tool_name,
            "input": input_data,
        }
    )


def tool_output_available(tool_call_id: str, output: str) -> str:
    """SSE: tool execution result."""
    return sse_event(
        {"type": "tool-output-available", "toolCallId": tool_call_id, "output": output}
    )


def finish_event() -> str:
    """SSE: stream finished."""
    return sse_event({"type": "finish"})


def done_event() -> str:
    """SSE: [DONE] signal."""
    return sse_event("[DONE]")


def error_event(message: str) -> str:
    """SSE: error event."""
    return sse_event({"type": "error", "errorText": message})
