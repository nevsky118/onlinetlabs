"""Интерфейс среды-исполнителя. GNS3Actor — реальная реализация; fake-адаптер (follow-on)
реализует тот же Protocol для быстрого power-анализа."""
from typing import Protocol

from simulation.policy import Action


class Actor(Protocol):
    async def execute(
        self, action: Action, cmd: str = "", help_context: dict | None = None
    ) -> None:
        """Исполнить действие студента в среде."""
        ...
