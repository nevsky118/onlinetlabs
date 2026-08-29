from pydantic import BaseModel


class ChatStreamRequest(BaseModel):
    """Chat streaming request. Session id, messages, optional selected model."""

    id: str
    messages: list[dict]
    model_id: str | None = None


class ChatModelOption(BaseModel):
    """One selectable chat model."""

    id: str
    label: str


class ChatModelsResponse(BaseModel):
    """Model catalog for the UI. `models` is empty when selection is disallowed."""

    can_select: bool
    default_model_id: str
    models: list[ChatModelOption]
