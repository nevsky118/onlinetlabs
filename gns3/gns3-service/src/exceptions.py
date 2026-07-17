# Domain exceptions for gns3-service.
#
# Inherit from ValueError for backward compatibility with tests and old
# router checks. Handlers in main.py translate them into HTTP 404 and 409.


class SessionNotFound(ValueError):
    """Session not found in the DB."""


class SessionClosed(ValueError):
    """Session is already closed, operation not possible."""
