"""Test data for the database seam: session factory doubles."""

from unittest.mock import AsyncMock


class StubDbContextData:
    """Async context manager that yields a mock session."""

    async def __aenter__(self):
        return AsyncMock()

    async def __aexit__(self, *exc):
        return False


class StubDbFactoryData:
    """Stand-in for the async session factory: every call opens a mock session."""

    def __call__(self):
        return StubDbContextData()
