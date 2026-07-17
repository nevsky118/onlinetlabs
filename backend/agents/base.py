"""Base class for all platform agents."""

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from config.config_model import ConfigModel, LlmProvider
from core.llm.client import build_client, model_uri, resolve_model


class BaseAgent:
    """Base agent. Subclasses override system_prompt() and run()."""

    def __init__(self, config: ConfigModel):
        self.config = config
        self.agents_config = config.agents

    def _agent_for(self, model_id: str) -> Agent:
        """Fresh pydantic-ai Agent for model_id (2.x supports model= per run, no cache needed)."""
        return Agent(model=self._build_model(model_id), system_prompt=self.system_prompt())

    def _build_model(self, model_id: str) -> OpenAIChatModel:
        """OpenAI-compatible model (yandex/openrouter) from provider credentials."""
        creds, _ = resolve_model(model_id)
        if creds.provider == LlmProvider.YANDEX and not creds.yandex_folder:
            raise ValueError(f"yandex_folder required for YANDEX provider, model {model_id}")
        client = build_client(model_id)
        return OpenAIChatModel(model_uri(model_id), provider=OpenAIProvider(openai_client=client))

    def system_prompt(self) -> str:
        """System prompt. Overridden in each agent."""
        raise NotImplementedError

    async def run(self, input_data: BaseModel) -> BaseModel:
        """Main method. Overridden in each agent."""
        raise NotImplementedError
