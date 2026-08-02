"""Domain exceptions for gns3-service.

Subclass ValueError so existing router checks still catch them; main.py maps
them to 404 and 409.
"""


class SessionNotFound(ValueError):
    """Session not found in the DB."""


class SessionClosed(ValueError):
    """Session is already closed, operation not possible."""
