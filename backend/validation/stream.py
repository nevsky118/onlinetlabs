"""SSE serialization of validation events."""

import json
from dataclasses import dataclass, field


@dataclass
class Event:
    """A validation event with a type and payload to send to the client."""

    type: str
    data: dict = field(default_factory=dict)

    def to_sse(self) -> str:
        """Serialize the event into an SSE-formatted string."""
        payload = {"type": self.type, **self.data}
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
