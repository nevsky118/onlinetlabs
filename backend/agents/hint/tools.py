"""Инструменты HintAgent."""

MAX_HINTS = 3


class HintTools:
    """Инструменты для генерации прогрессивных подсказок."""

    def get_hint_level(self, attempts_count: int) -> int:
        """Определить уровень подсказки по кол-ву попыток."""
        if attempts_count <= 1:
            return 1
        elif attempts_count <= 3:
            return 2
        else:
            return 3

    def get_remaining_hints(self, current_level: int) -> int:
        """Сколько уровней подсказок осталось."""
        return max(0, MAX_HINTS - current_level)

