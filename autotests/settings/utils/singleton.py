# Метакласс Singleton (потокобезопасный).

from threading import Lock


class Singleton(type):
    """
    Метакласс, реализующий паттерн Singleton.

    Потокобезопасен. При повторных вызовах возвращает уже созданный экземпляр
    и повторно вызывает __init__ с новыми аргументами.
    """

    _instances = {}
    _lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
            else:
                cls._instances[cls].__init__(*args, **kwargs)
        return cls._instances[cls]
