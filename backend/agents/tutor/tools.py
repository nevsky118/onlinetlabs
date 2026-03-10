"""Инструменты TutorAgent."""


class TutorTools:
    """Инструменты для получения контекста лабы и курса."""

    def __init__(self, mcp_client=None):
        self._mcp = mcp_client

    async def get_lab_context(self, lab_slug: str) -> str:
        """Получить описание лабы для контекста ответа."""
        if not lab_slug:
            return ""
        return f"Lab: {lab_slug}"

    async def get_step_context(self, lab_slug: str, step_slug: str) -> str:
        """Получить описание шага для контекста ответа."""
        if not lab_slug or not step_slug:
            return ""
        return f"Lab: {lab_slug}, Step: {step_slug}"
