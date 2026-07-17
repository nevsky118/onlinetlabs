"""Interface for the executor environment. GNS3Actor is the real implementation; a fake
adapter (follow-on) implements the same Protocol for fast power analysis."""
from typing import Protocol

from simulation.policy import Action


class Actor(Protocol):
    async def execute(
        self, action: Action, cmd: str = "", help_context: dict | None = None
    ) -> None:
        """Execute the student's action in the environment."""
        ...
