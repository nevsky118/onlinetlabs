from pydantic import BaseModel


class ChatStreamRequest(BaseModel):
    """Запрос на стриминг чата. Id сессии, сообщения, опц. выбранная модель."""

    id: str
    messages: list[dict]
    model_id: str | None = None
