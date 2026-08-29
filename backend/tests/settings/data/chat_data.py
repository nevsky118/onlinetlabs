"""Test data for the chat model catalog: stand-ins for settings.agents."""


class ModelEntryData:
    """One entry of the model catalog."""

    def __init__(self, id: str, label: str = "", tools: bool = False):
        self.id = id
        self.label = label or id
        self.tools = tools


class AgentsCatalogData:
    """Stand-in for settings.agents: a default chat model plus a catalog to look up."""

    def __init__(self, chat_model: str, catalog: list | None = None, ids: set[str] | None = None):
        self.chat_model = chat_model
        self.catalog = (
            list(catalog)
            if catalog is not None
            else [ModelEntryData(model_id) for model_id in sorted(ids or ())]
        )

    def get_entry(self, model_id: str):
        """The catalog entry, or None when the id is unknown."""
        return next((entry for entry in self.catalog if entry.id == model_id), None)


class SettingsWithAgentsData:
    """Stand-in for settings carrying nothing but .agents."""

    def __init__(self, agents):
        self.agents = agents
