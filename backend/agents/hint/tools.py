"""HintAgent tools."""

MAX_HINTS = 3


class HintTools:
    """Tools for generating progressive hints."""

    def get_hint_level(self, attempts_count: int) -> int:
        """Determine hint level from attempt count."""
        if attempts_count <= 1:
            return 1
        elif attempts_count <= 3:
            return 2
        else:
            return 3

    def get_remaining_hints(self, current_level: int) -> int:
        """How many hint levels remain."""
        return max(0, MAX_HINTS - current_level)
