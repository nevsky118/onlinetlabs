from pydantic import BaseModel


class ChatStreamRequest(BaseModel):
    """Запрос на стриминг чата. Id сессии и список сообщений."""

    id: str
    messages: list[dict]
