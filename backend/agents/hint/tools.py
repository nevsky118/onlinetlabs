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

    def generate_hint(
        self, step_slug: str, hint_level: int, last_error: str | None
    ) -> str:
        """Сгенерировать подсказку нужного уровня."""
        if hint_level == 1:
            return f"Подсказка уровня 1 для {step_slug}: проверь основные настройки."
        elif hint_level == 2:
            error_ctx = f" Последняя ошибка: {last_error}." if last_error else ""
            return (
                f"Подсказка уровня 2 для {step_slug}: "
                f"обрати внимание на конфигурацию компонентов.{error_ctx}"
            )
        else:
            error_ctx = f" Ошибка: {last_error}." if last_error else ""
            return (
                f"Подсказка уровня 3 для {step_slug}: "
                f"конкретный шаг — проверь связность и статусы.{error_ctx}"
            )
