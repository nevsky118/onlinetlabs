# Singleton metaclass (thread-safe).

from threading import Lock


class Singleton(type):
    """
    Metaclass implementing the Singleton pattern.

    Thread-safe. On repeated calls it returns the already created instance
    and calls __init__ again with the new arguments.
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
