"""TutorAgent tools."""


class TutorTools:
    """Tools for fetching lab and course context."""

    def __init__(self, mcp_client=None):
        """Stores the optional MCP client for fetching context."""
        self._mcp = mcp_client

    async def get_lab_context(self, lab_slug: str) -> str:
        """Get lab description for answer context."""
        if not lab_slug:
            return ""
        return f"Lab: {lab_slug}"

    async def get_step_context(self, lab_slug: str, step_slug: str) -> str:
        """Get step description for answer context."""
        if not lab_slug or not step_slug:
            return ""
        return f"Lab: {lab_slug}, Step: {step_slug}"
