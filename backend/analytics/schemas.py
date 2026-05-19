import json
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class EventPayload(BaseModel):
    """Одно событие телеметрии платформы."""

    event_name: str = Field(max_length=100)
    properties: dict = Field(default_factory=dict)
    session_id: str | None = None
    client_ts: datetime

    @field_validator("properties")
    @classmethod
    def limit_properties_size(cls, v: dict) -> dict:
        """Проверяет, что размер properties не превышает 4 КБ."""
        if len(json.dumps(v)) > 4096:
            raise ValueError("properties exceeds 4KB")
        return v


class AnalyticsIngestRequest(BaseModel):
    """Запрос на приём пачки событий телеметрии от устройства."""

    device_id: str = Field(max_length=100)
    events: list[EventPayload] = Field(min_length=1, max_length=50)
