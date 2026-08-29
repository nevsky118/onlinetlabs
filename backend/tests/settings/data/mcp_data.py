"""Test data for the MCP seam: a client that answers with prepared lists."""


class McpClientData:
    """An MCP client returning fixed answers. An Exception value is raised instead."""

    def __init__(self, components=None, actions=None, errors=None):
        self.components = components if components is not None else []
        self.actions = actions if actions is not None else []
        self.errors = errors if errors is not None else []

    @staticmethod
    def _answer(value):
        """Raises when the prepared answer is an exception, else returns it."""
        if isinstance(value, Exception):
            raise value
        return value

    async def list_components(self, ctx):
        """The prepared components."""
        return self._answer(self.components)

    async def list_user_actions(self, ctx, limit: int = 10):
        """The prepared actions, capped at `limit`."""
        return self._answer(self.actions)[:limit]

    async def list_errors(self, ctx, since=None):
        """The prepared errors."""
        return self._answer(self.errors)
