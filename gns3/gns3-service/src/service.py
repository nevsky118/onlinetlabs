# Re-export-фасад для обратной совместимости импортов.
#
# Реализация SessionService переехала в src/services/. Этот модуль оставлен,
# чтобы не ломать тесты и сторонних потребителей, импортирующих из src.service.

from src.services.session_lifecycle import SessionService

__all__ = ["SessionService"]
