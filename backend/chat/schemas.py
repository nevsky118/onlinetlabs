from pydantic import BaseModel


class ChatStreamRequest(BaseModel):
    """Chat streaming request. Session id, messages, optional selected model."""

    id: str
    messages: list[dict]
    model_id: str | None = None
