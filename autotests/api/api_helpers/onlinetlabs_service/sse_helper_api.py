# Helper methods for reading a Server-Sent Events stream.

import json


class SseHelper:
    """Parses the SSE lines a streaming endpoint returns."""

    DATA_PREFIX = "data:"
    DONE = "[DONE]"

    @classmethod
    def parse_events(cls, lines: list[str]) -> tuple[list[dict], bool]:
        """Returns the decoded events and whether the stream signalled [DONE]."""
        events: list[dict] = []
        done = False
        for line in lines:
            if not line.startswith(cls.DATA_PREFIX):
                continue
            payload = line[len(cls.DATA_PREFIX) :].strip()
            if payload == cls.DONE:
                done = True
                continue
            try:
                events.append(json.loads(payload))
            except json.JSONDecodeError:
                continue
        return events, done

    @classmethod
    def parse_event_types(cls, lines: list[str]) -> tuple[set[str], bool]:
        """Returns the set of event `type` values and whether the stream signalled [DONE]."""
        events, done = cls.parse_events(lines)
        types = {event["type"] for event in events if isinstance(event, dict) and "type" in event}
        return types, done
