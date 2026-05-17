# Доменные исключения gns3-service.
#
# Наследуются от ValueError ради обратной совместимости тестов и старых
# роутерных проверок. Обработчики в main.py переводят их в HTTP 404 и 409.


class SessionNotFound(ValueError):
    """Сессия не найдена в БД."""


class SessionClosed(ValueError):
    """Сессия уже закрыта, операция невозможна."""
