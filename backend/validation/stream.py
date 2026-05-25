"""SSE-сериализация событий валидации."""

import json
from dataclasses import dataclass, field


@dataclass
class Event:
    """Событие валидации с типом и полезной нагрузкой для отправки клиенту."""

    type: str
    data: dict = field(default_factory=dict)

    def to_sse(self) -> str:
        """Сериализовать событие в строку формата SSE."""
        payload = {"type": self.type, **self.data}
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
